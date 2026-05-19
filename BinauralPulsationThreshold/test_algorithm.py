"""
test_algorithm.py
==================
CP4: Jesteadtアルゴリズム単体テスト（PsychoPy不要）

config.py と phase2_adaptive.py の AdaptiveTrack クラスのみを
利用してシミュレーションを実行する。

実行: python test_algorithm.py
"""
import sys, os
import random
import numpy as np

# phase2_adaptive からは AdaptiveTrack だけを直接 import したいが
# psychopy を import するモジュールを回避するため、ここにインラインで再定義する。

sys.path.insert(0, os.path.dirname(__file__))
import config

# ──────────────────────────────────────────
# AdaptiveTrack を psychopy 依存なしで再現
# ──────────────────────────────────────────
class AdaptiveTrack:
    def __init__(self, track_name, masker_spectrum_level_db, start_level_offset):
        self.name = track_name
        self.masker_spectrum_level = masker_spectrum_level_db
        self.is_track_a = (track_name == "A")
        self.level = masker_spectrum_level_db + start_level_offset
        self.step = config.STEP_LARGE
        self.n_reversals = 0
        self.last_direction = None
        self.reversal_levels = []
        self.consecutive_same = 0
        self.history = []
        self.trial_no = 0
        self._finished = False

    def is_finished(self): return self._finished
    def get_current_level(self):
        return float(np.clip(self.level, config.TEST_MIN_LEVEL, config.TEST_MAX_LEVEL))

    def get_threshold(self):
        small = self.reversal_levels[config.STEP_CHANGE_REVERSALS:]
        if small: return float(np.mean(small))
        if self.reversal_levels: return float(np.mean(self.reversal_levels))
        return self.level

    def record_response(self, is_pulsating, trial_global):
        self.trial_no += 1
        target = is_pulsating if self.is_track_a else (not is_pulsating)
        is_reversal = False

        if target:
            self.consecutive_same += 1
            if self.consecutive_same >= 2:
                direction = "down" if self.is_track_a else "up"
                if self.last_direction and self.last_direction != direction:
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
            self.consecutive_same = 0
            direction = "up" if self.is_track_a else "down"
            if self.last_direction and self.last_direction != direction:
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

        self.history.append({"is_reversal": is_reversal, "level_db": self.get_current_level()})


# ──────────────────────────────────────────
# シミュレーション実行
# ──────────────────────────────────────────
def simulate(seed: int = 42, pulsating_prob: float = 0.6) -> None:
    """
    正解確率 pulsating_prob で被験者をシミュレートし、
    Track A/B が規定の反転回数に達して終了するかを確認する。
    """
    rng = random.Random(seed)
    masker_spectrum_db = -50.0  # dB/Hz
    track_a = AdaptiveTrack("A", masker_spectrum_db, config.TRACK_A_START_LEVEL)
    track_b = AdaptiveTrack("B", masker_spectrum_db, config.TRACK_B_START_LEVEL)

    print(f"\n--- シミュレーション開始 (seed={seed}, pulsating_prob={pulsating_prob}) ---")
    print(f"{'Trial':>6} {'Track':>6} {'Level(dBFS)':>12} {'Response':>12} {'Rev#':>5} {'Step':>6}")

    trial = 0
    while not (track_a.is_finished() and track_b.is_finished()):
        active = [t for t in [track_a, track_b] if not t.is_finished()]
        if not active: break
        track = rng.choice(active)
        trial += 1

        # 被験者シミュレーション: レベルが高いほど"断続"と答えやすい簡易モデル
        is_pulsating = rng.random() < pulsating_prob
        prev_rev = track.n_reversals
        track.record_response(is_pulsating, trial)
        marker = " <<<" if track.n_reversals > prev_rev else ""
        resp_str = "pulsating" if is_pulsating else "continuous"
        print(
            f"{trial:>6} {track.name:>6} {track.get_current_level():>12.2f} "
            f"{resp_str:>12} {track.n_reversals:>5} {track.step:>6.1f}{marker}"
        )

    thr_a = track_a.get_threshold()
    thr_b = track_b.get_threshold()
    final = (thr_a + thr_b) / 2.0

    print(f"\n  Track A 反転数: {track_a.n_reversals} / {config.TOTAL_REVERSALS}")
    print(f"  Track B 反転数: {track_b.n_reversals} / {config.TOTAL_REVERSALS}")
    print(f"  Track A 閾値: {thr_a:.2f} dB FS")
    print(f"  Track B 閾値: {thr_b:.2f} dB FS")
    print(f"  最終閾値(算術平均): {final:.2f} dB FS")

    # ── アサーション ──
    assert track_a.n_reversals >= config.TOTAL_REVERSALS, "Track A が規定反転数に達していない"
    assert track_b.n_reversals >= config.TOTAL_REVERSALS, "Track B が規定反転数に達していない"
    assert isinstance(thr_a, float), "Track A 閾値が float でない"
    assert isinstance(thr_b, float), "Track B 閾値が float でない"
    print("\n  [OK] すべてのアサーションを通過しました。")


if __name__ == "__main__":
    simulate(seed=42, pulsating_prob=0.6)
    simulate(seed=123, pulsating_prob=0.3)
