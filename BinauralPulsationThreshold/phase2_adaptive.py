# -*- coding: utf-8 -*-
"""
phase2_adaptive.py
==================
Phase 2: Jesteadt (1980) 2系列適応的アルゴリズム

Track A（高レベル開始）: 「断続」と71%の確率で回答されるレベルを探索
  - 「断続」2連続 → レベルを下げる
  - 「連続」1回   → レベルを上げる

Track B（低レベル開始）: 「連続」と71%の確率で回答されるレベルを探索
  - 「連続」2連続 → レベルを上げる
  - 「断続」1回   → レベルを下げる
"""

import random
import numpy as np
from psychopy import visual, sound, core, event

import config
from phase2_stimulus import build_alternating_stimulus


# ────────────────────────────────────────────
# 単一トラック クラス
# ────────────────────────────────────────────

class AdaptiveTrack:
    """
    Jesteadt (1980) の1トラック分の適応的測定を管理するクラス。

    Parameters
    ----------
    track_name : str
        "A" または "B"。
    masker_spectrum_level_db : float
        マスカーのスペクトルレベル (dB/Hz)。
    start_level_offset : float
        開始テスト信号レベル = masker_spectrum_level_db + 10*log10(BW) + start_level_offset (dB) に相当するが、
        現状は masker_spectrum_level_db に対する直接のオフセットとして扱う。
    """

    def __init__(
        self,
        track_name: str,
        masker_spectrum_level_db: float,
        start_level_offset: float,
    ) -> None:
        self.name = track_name
        self.masker_spectrum_level = masker_spectrum_level_db

        # Track A: 下げる方向, Track B: 上げる方向
        self.is_track_a = (track_name == "A")

        self.level = masker_spectrum_level_db + start_level_offset
        self.step = config.STEP_LARGE

        self.n_reversals = 0
        self.last_direction: str | None = None  # "up" | "down"
        self.reversal_levels: list[float] = []

        self.consecutive_same = 0  # 連続同一回答カウント
        self.history: list[dict] = []  # 全試行の記録
        self.trial_no = 0
        self._finished = False

    # ── 終了判定 ──
    def is_finished(self) -> bool:
        return self._finished

    # ── 現在レベルの取得 ──
    def get_current_level(self) -> float:
        return float(np.clip(self.level, config.TEST_MIN_LEVEL, config.TEST_MAX_LEVEL))

    # ── 閾値算出（最終ステップ幅での反転点の平均）──
    def get_threshold(self) -> float:
        small_step_revs = self.reversal_levels[config.STEP_CHANGE_REVERSALS:]
        if small_step_revs:
            return float(np.mean(small_step_revs))
        if self.reversal_levels:
            return float(np.mean(self.reversal_levels))
        return self.level

    # ── 応答を記録してレベルを更新 ──
    def record_response(self, is_pulsating: bool, trial_global: int) -> None:
        """
        被験者の回答を受け取り、次試行のレベルを決定する。

        Parameters
        ----------
        is_pulsating : bool
            True = 「断続」、False = 「連続」と回答。
        trial_global : int
            全体試行番号（CSVへの記録用）。
        """
        self.trial_no += 1

        if self.is_track_a:
            # Track A の目標回答: 「断続」
            target_response = is_pulsating  # True = 目標
        else:
            # Track B の目標回答: 「連続」
            target_response = not is_pulsating  # True = 目標

        is_reversal = False

        if target_response:
            self.consecutive_same += 1
            if self.consecutive_same >= 2:
                # 2連続 → Track A: 下げる, Track B: 上げる
                direction = "down" if self.is_track_a else "up"
                if self.last_direction is not None and self.last_direction != direction:
                    self.n_reversals += 1
                    self.reversal_levels.append(self.level)
                    is_reversal = True
                    if self.n_reversals == config.STEP_CHANGE_REVERSALS:
                        self.step = config.STEP_SMALL
                    if self.n_reversals >= config.TOTAL_REVERSALS:
                        self._finished = True

                self.level += -self.step if self.is_track_a else self.step
                self.level = float(np.clip(self.level, config.TEST_MIN_LEVEL, config.TEST_MAX_LEVEL))
                self.last_direction = direction
                self.consecutive_same = 0
        else:
            # 1回でも外れ → Track A: 上げる, Track B: 下げる
            direction = "up" if self.is_track_a else "down"
            if self.last_direction is not None and self.last_direction != direction:
                self.n_reversals += 1
                self.reversal_levels.append(self.level)
                is_reversal = True
                if self.n_reversals == config.STEP_CHANGE_REVERSALS:
                    self.step = config.STEP_SMALL
                if self.n_reversals >= config.TOTAL_REVERSALS:
                    self._finished = True

            self.level += self.step if self.is_track_a else -self.step
            self.level = float(np.clip(self.level, config.TEST_MIN_LEVEL, config.TEST_MAX_LEVEL))
            self.last_direction = direction
            self.consecutive_same = 0

        self.history.append({
            "track": self.name,
            "trial_global": trial_global,
            "track_trial": self.trial_no,
            "level_db": self.get_current_level(),
            "is_pulsating": is_pulsating,
            "is_reversal": is_reversal,
        })


# ────────────────────────────────────────────
# 1ITD条件のトライアルループ
# ────────────────────────────────────────────

def run_itd_condition(
    win: visual.Window,
    masker_spectrum_level_db: float,
    itd_seconds: float,
    subject_id: str,
    itd_label_us: int,
    recorder,          # data_recorder.DataRecorder
    sl_reference_db: float,
    test_freq: float,
    mod_freq: float,
    mod_type: str,
    masker_itd_sec: float,
    masker_itd_us: int,
) -> tuple[float, float]:
    """
    1つのITD条件について Track A/B をインターリーブで実行する。

    Parameters
    ----------
    win : psychopy.visual.Window
    masker_spectrum_level_db : float
        マスカーのスペクトルレベル (dB/Hz)。
    itd_seconds : float
        ITD (秒)。
    subject_id : str
    itd_label_us : int
        CSV記録に用いるITDラベル (µs)。
    recorder : DataRecorder
        データ記録オブジェクト。
    sl_reference_db : float
        1kHz聴取閾値基準 (dB FS)
    test_freq : float
        テスト信号周波数 (Hz)
    mod_freq : float
        変調周波数 (Hz)
    mod_type : str
        変調タイプ
    masker_itd_sec : float
        マスカーのITD (秒)
    masker_itd_us : int
        マスカーのITD (µs)

    Returns
    -------
    (threshold_A, threshold_B) : tuple[float, float]
        Track AとBそれぞれの推定閾値 (dB FS)。
    """
    track_a = AdaptiveTrack("A", masker_spectrum_level_db, config.TRACK_A_START_LEVEL)
    track_b = AdaptiveTrack("B", masker_spectrum_level_db, config.TRACK_B_START_LEVEL)

    # ── 教示画面 ──
    instr = visual.TextStim(
        win,
        text=(
            f"ITD = {itd_label_us} µs\n\n"
            "Discontinuous (断続) と聴こえたら → [D] キー\n"
            "Continuous (連続) と聴こえたら   → [C] キー\n\n"
            "[スペース] で開始"
        ),
        height=0.06, wrapWidth=1.5, color="white",
    )
    instr.draw()
    win.flip()
    event.waitKeys(keyList=["space"])

    prompt = visual.TextStim(win, text="", height=0.08, color="white")
    trial_global = 0

    while not (track_a.is_finished() and track_b.is_finished()):
        # 未終了のTrackからランダム選択
        active = [t for t in [track_a, track_b] if not t.is_finished()]
        if not active:
            break
        track = random.choice(active)
        trial_global += 1

        level = track.get_current_level()

        # ── 刺激生成・再生 ──
        stim_array = build_alternating_stimulus(
            masker_spectrum_level_db, level, itd_seconds,
            test_freq=test_freq, mod_freq=mod_freq, mod_type=mod_type, masker_itd_sec=masker_itd_sec
        )
        snd = sound.Sound(
            value=stim_array,
            sampleRate=config.SAMPLE_RATE,
            stereo=True,
        )

        prompt.text = "聴いてください..."
        prompt.draw()
        win.flip()

        event.clearEvents()
        snd.play()
        stim_duration = stim_array.shape[0] / config.SAMPLE_RATE
        core.wait(stim_duration)
        snd.stop()
        snd = None  # 明示的に解放してオーディオバッファの残留を防ぐ

        # ── 応答収集 ──
        prompt.text = "Discontinuous (断続) → [D]     Continuous (連続) → [C]"
        prompt.draw()
        win.flip()

        keys = event.waitKeys(
            keyList=[config.KEY_PULSATING, config.KEY_CONTINUOUS, "escape"],
        )

        if keys[0] == "escape":
            win.close()
            core.quit()
        else:
            is_pulsating = (keys[0] == config.KEY_PULSATING)

        # ── トラック更新 ──
        track.record_response(is_pulsating, trial_global)

        # ── データ記録 ──
        last = track.history[-1]
        recorder.add_trial(
            subject_id=subject_id,
            sl_reference_db=sl_reference_db,
            test_freq=test_freq,
            mod_freq=mod_freq,
            mod_type=mod_type,
            masker_itd_us=masker_itd_us,
            itd_us=itd_label_us,
            track=last["track"],
            trial_no=last["trial_global"],
            level_db=last["level_db"],
            response="pulsating" if last["is_pulsating"] else "continuous",
            is_reversal=last["is_reversal"],
        )

        # ── 短インターバル ──
        prompt.text = ""
        prompt.draw()
        win.flip()
        core.wait(0.3)

    return track_a.get_threshold(), track_b.get_threshold()


# ────────────────────────────────────────────
# アルゴリズム単体テスト（`python phase2_adaptive.py` で実行）
# ────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    print("=== Track A/B 単体シミュレーション ===")
    masker_spectrum_db = -50.0  # dB/Hz
    track_a = AdaptiveTrack("A", masker_spectrum_db, config.TRACK_A_START_LEVEL)
    track_b = AdaptiveTrack("B", masker_spectrum_db, config.TRACK_B_START_LEVEL)

    rng = random.Random(42)
    trial = 0
    while not (track_a.is_finished() and track_b.is_finished()):
        active = [t for t in [track_a, track_b] if not t.is_finished()]
        if not active:
            break
        track = rng.choice(active)
        trial += 1

        # ランダム応答（デモ用）
        is_pulsating = rng.random() > 0.5
        track.record_response(is_pulsating, trial)

        last = track.history[-1]
        marker = " <<< reversal" if last["is_reversal"] else ""
        print(
            f"Trial {trial:3d} | Track {track.name} "
            f"| level={last['level_db']:7.2f} dB "
            f"| {'pulsating' if last['is_pulsating'] else 'continuous '}"
            f"| rev={track.n_reversals}{marker}"
        )

    print(f"\nTrack A 閾値: {track_a.get_threshold():.2f} dB FS")
    print(f"Track B 閾値: {track_b.get_threshold():.2f} dB FS")
    print(f"最終閾値(算術平均): {(track_a.get_threshold() + track_b.get_threshold()) / 2:.2f} dB FS")
    print("シミュレーション完了")
