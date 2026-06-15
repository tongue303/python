# -*- coding: utf-8 -*-
"""
phase2_1up1down.py
==================
Phase 2: Experiment C 準拠の 1-up/1-down 階段法 (Staircase method)
被験者が「50%の確率で連続していると知覚するターゲット音のレベル」を探索する。
"""

import random
import numpy as np
from psychopy import visual, sound, core, event

import config
from phase2_stimulus import build_alternating_stimulus


class AdaptiveTrack1Up1Down:
    """
    1-up/1-down 階段法アルゴリズム (Experiment C準拠) を管理するクラス。
    """
    def __init__(self, masker_spectrum_level_db: float):
        self.masker_spectrum_level = masker_spectrum_level_db
        
        # 初期ターゲットレベル：確実に途切れて聞こえる高いレベル
        # config.ADAPTIVE_INITIAL_TARGET_OFFSET を目安に、± Roving_Range のジッターを加える
        jitter = random.uniform(-config.ADAPTIVE_ROVING_RANGE, config.ADAPTIVE_ROVING_RANGE)
        initial_target_level = masker_spectrum_level_db + config.ADAPTIVE_INITIAL_TARGET_OFFSET + jitter
        
        # リミッター適用
        self.current_target_level = float(np.clip(
            initial_target_level, 
            config.TEST_MIN_LEVEL, 
            config.TEST_MAX_LEVEL
        ))
        
        self.current_step_size = config.ADAPTIVE_INITIAL_STEP_SIZE
        self.reversal_count = 0
        self.previous_direction = None  # 1 (UP) or -1 (DOWN)
        self.reversal_levels = []
        
        self.history = []
        self.trial_no = 0
        self._finished = False

    def is_finished(self) -> bool:
        return self._finished

    def get_current_level(self) -> float:
        return self.current_target_level

    def get_threshold(self) -> float:
        """
        最後の6回分（インデックス4〜9）の算術平均を閾値として算出する
        """
        if len(self.reversal_levels) < config.ADAPTIVE_MAX_REVERSALS:
            # 万が一途中で終わった場合のフォールバック
            return float(np.mean(self.reversal_levels)) if self.reversal_levels else self.current_target_level
            
        start_idx = config.ADAPTIVE_MAX_REVERSALS - config.ADAPTIVE_NUM_REVERSALS_FOR_MEAN
        target_revs = self.reversal_levels[start_idx:]
        return float(np.mean(target_revs))

    def record_response(self, is_continuous: bool, trial_global: int) -> None:
        """
        被験者の回答に応じてロジックを進行する
        """
        self.trial_no += 1
        is_reversal = False
        
        # Step 1: レベル変更方向の決定
        if is_continuous:
            # 錯覚が起きている -> ターゲットレベルが低すぎる -> UP (+1)
            current_direction = 1
        else:
            # 途切れて聞こえた -> ターゲットレベルが高すぎる -> DOWN (-1)
            current_direction = -1

        next_target_level = self.current_target_level + (current_direction * self.current_step_size)
        
        # Step 2: 反転判定
        if self.previous_direction is not None and current_direction != self.previous_direction:
            # 反転発生
            self.reversal_count += 1
            self.reversal_levels.append(self.current_target_level)
            is_reversal = True
            
            # Step 3: ステップ幅の更新
            if self.reversal_count == config.ADAPTIVE_REVERSAL_TRIGGER_1:
                self.current_step_size = config.ADAPTIVE_SECOND_STEP_SIZE
            elif self.reversal_count == config.ADAPTIVE_REVERSAL_TRIGGER_2:
                self.current_step_size = config.ADAPTIVE_FINAL_STEP_SIZE

        # 履歴記録
        self.history.append({
            "trial_global": trial_global,
            "level_db": self.current_target_level,
            "response": "continuous" if is_continuous else "interrupted",
            "is_reversal": is_reversal,
            "reversal_count": self.reversal_count,
            "step_size": self.current_step_size
        })

        # Step 4: 終了判定とステータス更新
        self.previous_direction = current_direction
        
        if self.reversal_count >= config.ADAPTIVE_MAX_REVERSALS:
            self._finished = True
        else:
            self.current_target_level = float(np.clip(
                next_target_level, 
                config.TEST_MIN_LEVEL, 
                config.TEST_MAX_LEVEL
            ))


def run_1up1down_condition(
    win: visual.Window,
    masker_spectrum_level_db: float,
    itd_seconds: float,
    subject_id: str,
    itd_label_us: int,
    recorder,
    sl_reference_db: float,
    test_freq: float,
    mod_freq: float,
    mod_type: str,
    masker_itd_sec: float,
    masker_itd_us: int,
) -> tuple[float, list[float]]:
    """
    1つのITD条件について、1-up 1-down 適応法を実行する。
    """
    track = AdaptiveTrack1Up1Down(masker_spectrum_level_db)

    # ── 教示画面 ──
    instr = visual.TextStim(
        win,
        text=(
            f"ITD = {itd_label_us} µs\n\n"
            f"Continuous (連続) と聴こえたら   → [{config.KEY_CONTINUOUS.upper()}] キー\n"
            f"Interrupted (断続) と聴こえたら → [{config.KEY_INTERRUPTED.upper()}] キー\n\n"
            "[スペース] で開始"
        ),
        height=0.06, wrapWidth=1.5, color="white",
    )
    instr.draw()
    win.flip()
    event.waitKeys(keyList=["space"])

    prompt = visual.TextStim(win, text="", height=0.08, color="white")
    trial_global = 0

    while not track.is_finished():
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
        snd = None

        # ── 応答収集 ──
        prompt.text = f"Continuous (連続) → [{config.KEY_CONTINUOUS.upper()}]     Interrupted (断続) → [{config.KEY_INTERRUPTED.upper()}]"
        prompt.draw()
        win.flip()

        keys = event.waitKeys(
            keyList=[config.KEY_CONTINUOUS, config.KEY_INTERRUPTED, "escape"],
        )

        if keys[0] == "escape":
            win.close()
            core.quit()
        else:
            is_continuous = (keys[0] == config.KEY_CONTINUOUS)

        # ── トラック更新 ──
        track.record_response(is_continuous, trial_global)

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
            track="1up1down",
            trial_no=last["trial_global"],
            level_db=last["level_db"],
            response=last["response"],
            is_reversal=last["is_reversal"],
        )

        # ── 短インターバル ──
        prompt.text = ""
        prompt.draw()
        win.flip()
        core.wait(0.3)

    final_threshold = track.get_threshold()
    reversal_levels = track.reversal_levels

    return final_threshold, reversal_levels

if __name__ == "__main__":
    print("=== 1-up/1-down 単体シミュレーション ===")
    masker_spectrum_db = -50.0
    track = AdaptiveTrack1Up1Down(masker_spectrum_db)

    rng = random.Random(42)
    trial = 0
    while not track.is_finished():
        trial += 1
        
        # 適当なPsychometric function (例: -45 dB を閾値とする)
        # level が -45 より大きければ連続して聞こえやすい
        level = track.get_current_level()
        prob_continuous = 1.0 / (1.0 + np.exp(-0.5 * (level - (-45.0))))
        
        is_continuous = rng.random() < prob_continuous
        track.record_response(is_continuous, trial)

        last = track.history[-1]
        marker = " <<< reversal" if last["is_reversal"] else ""
        print(
            f"Trial {trial:3d} | level={last['level_db']:7.2f} dB | step={last['step_size']:4.1f} "
            f"| resp={last['response']:11s} | rev_cnt={last['reversal_count']}{marker}"
        )

    print(f"\nシミュレーション完了")
    print(f"Reversal Levels: {[f'{v:.2f}' for v in track.reversal_levels]}")
    print(f"算出閾値: {track.get_threshold():.2f} dB FS")
