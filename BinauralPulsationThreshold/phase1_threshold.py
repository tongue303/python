# -*- coding: utf-8 -*-
"""
phase1_threshold.py
===================
Phase 1: 1kHz純音を用いた聴取閾値測定モジュール

収束ルール: 2-down 1-up
  - 正答2連続 → レベルを下げる
  - 誤答1回   → レベルを上げる
終了条件: 反転 PHASE1_TOTAL_REVERSALS 回
"""

import numpy as np
from psychopy import visual, sound, core, event

import config


# ────────────────────────────────────────────
# 1kHz 純音生成
# ────────────────────────────────────────────

def generate_1khz_tone(level_db_fs: float, duration: float = config.PHASE1_DURATION) -> np.ndarray:
    """
    1kHz 純音（両耳同位相ステレオ、コサインテーパー付き）を生成する。

    Parameters
    ----------
    level_db_fs : float
        提示レベル (dB FS)。0 dB FS = フルスケール振幅 1.0。
    duration : float
        音の長さ（秒）。

    Returns
    -------
    np.ndarray
        shape (n_samples, 2) の float32 ステレオ波形。
    """
    sr = config.SAMPLE_RATE
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    # 正弦波生成
    amplitude = 10 ** (level_db_fs / 20.0)
    wave = amplitude * np.sin(2 * np.pi * config.PHASE1_FREQ * t)

    # コサインテーパー（立ち上がり・立ち下がり）
    ramp_n = int(sr * config.RAMP_DURATION)
    ramp = 0.5 * (1 - np.cos(np.pi * np.arange(ramp_n) / ramp_n))
    wave[:ramp_n] *= ramp
    wave[-ramp_n:] *= ramp[::-1]

    # ステレオ化 (両耳同位相)
    stereo = np.column_stack([wave, wave]).astype(np.float64)
    return stereo


# ────────────────────────────────────────────
# Phase 1 メイン関数
# ────────────────────────────────────────────

def run_phase1(win: visual.Window) -> float:
    """
    1kHz 純音の聴取閾値を 2-down 1-up 階段法で測定する。

    Parameters
    ----------
    win : psychopy.visual.Window
        既存の PsychoPy ウィンドウ。

    Returns
    -------
    float
        推定閾値 (dB FS)。
    """
    sr = config.SAMPLE_RATE

    # ── 画面テキスト ──
    instr = visual.TextStim(
        win,
        text=(
            "Phase 1: 聴取閾値測定\n\n"
            "音が鳴り終わると「聴こえましたか？」と表示されます。\n"
            "聴こえたら [Y] ・ 聴こえなかったら [N] を押してください。\n\n"
            "準備ができたら [スペース] を押してください。"
        ),
        height=0.06, wrapWidth=1.5, color="white",
    )
    instr.draw()
    win.flip()
    event.waitKeys(keyList=["space"])

    prompt = visual.TextStim(win, text="", height=0.08, color="white")

    # ── 内部状態 ──
    current_level = config.PHASE1_START_LEVEL
    step = config.PHASE1_STEP_LARGE

    consecutive_correct = 0   # 正答連続カウント（2-down 1-up 用）
    n_reversals = 0
    last_direction = None       # "up" | "down"
    reversal_levels: list[float] = []

    trial_no = 0
    while n_reversals < config.PHASE1_TOTAL_REVERSALS:
        trial_no += 1

        # ── 刺激呈示 ──
        wave = generate_1khz_tone(current_level)
        snd = sound.Sound(
            value=wave,
            sampleRate=sr,
            stereo=True,
        )

        prompt.text = "聴いてください..."
        prompt.draw()
        win.flip()

        # 音を再生し、終了まで待つ
        event.clearEvents()
        snd.play()
        core.wait(config.PHASE1_DURATION)
        snd.stop()
        snd = None  # 明示的に解放してオーディオバッファの残留を防ぐ

        # ── 音終了後に Y/N 質問を表示 ──
        prompt.text = "聴こえましたか？    [Y] はい    [N] いいえ"
        prompt.draw()
        win.flip()

        event.clearEvents()
        keys = event.waitKeys(
            keyList=[config.KEY_PHASE1_YES, config.KEY_PHASE1_NO, "escape"],
        )

        if keys[0] == "escape":
            win.close()
            core.quit()

        responded = (keys[0] == config.KEY_PHASE1_YES)  # Y = 聴こえた

        # ── 応答後の待機 ──
        prompt.text = ""
        prompt.draw()
        win.flip()
        core.wait(0.3)

        # ── 2-down 1-up ルール ──
        if responded:
            # 正答: 2連続正答でレベルを下げる
            consecutive_correct += 1
            if consecutive_correct >= 2:
                if last_direction == "up":
                    n_reversals += 1
                    reversal_levels.append(current_level)
                    if n_reversals == config.PHASE1_STEP_CHANGE_REVERSALS:
                        step = config.PHASE1_STEP_SMALL
                current_level -= step
                last_direction = "down"
                consecutive_correct = 0
        else:
            # 誤答（無反応）: 1回でレベルを上げる
            consecutive_correct = 0
            if last_direction == "down":
                n_reversals += 1
                reversal_levels.append(current_level)
                if n_reversals == config.PHASE1_STEP_CHANGE_REVERSALS:
                    step = config.PHASE1_STEP_SMALL
            current_level += step
            last_direction = "up"

        # ── レベル境界チェック（スタック防止）──
        # 下限に当たった場合: 次回は上方向とみなしてバウンス
        if current_level < config.PHASE1_MIN_LEVEL:
            current_level = config.PHASE1_MIN_LEVEL
            last_direction = "up"      # 次にミスしたとき反転として検出される
            consecutive_correct = 0
        # 上限に当たった場合: 次回は下方向とみなしてバウンス
        elif current_level > config.PHASE1_MAX_LEVEL:
            current_level = config.PHASE1_MAX_LEVEL
            last_direction = "down"
            consecutive_correct = 0

    # ── 閾値算出: 最終ステップ幅（STEP_SMALL）での反転点の平均 ──
    # ステップ縮小後の反転点のみを使用
    small_step_reversals = reversal_levels[config.PHASE1_STEP_CHANGE_REVERSALS:]
    if small_step_reversals:
        threshold = float(np.mean(small_step_reversals))
    else:
        threshold = float(np.mean(reversal_levels))

    # ── 完了メッセージ ──
    msg = visual.TextStim(
        win,
        text=(
            f"Phase 1 完了\n\n"
            f"推定閾値: {threshold:.1f} dB FS\n\n"
            f"[スペース] で次へ進んでください。"
        ),
        height=0.06, wrapWidth=1.5, color="white",
    )
    msg.draw()
    win.flip()
    event.waitKeys(keyList=["space"])

    return threshold


# ────────────────────────────────────────────
# CP2: 単体テスト用エントリーポイント
# ────────────────────────────────────────────

if __name__ == "__main__":
    from psychopy import visual, core

    win = visual.Window(
        size=(1600, 900),
        fullscr=False,
        color="black",
        units="norm",
        screen=0,
    )
    win.setMouseVisible(False)

    threshold = run_phase1(win)
    print(f"\nCP2 完了: 推定閾値 = {threshold:.2f} dB FS")

    win.close()
    core.quit()
