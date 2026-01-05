from .stimulus import PulsationSequence, PureToneStimulus, SilentStimulus
from .adaptive import AdaptiveStaircase, ThreeDownOneUpStaircase
import random
import numpy as np

class AbsoluteThresholdExperiment:
    """
    可聴閾値（Absolute Threshold）の測定実験
    
    手法: 2-Interval Forced Choice (2IFC)
    適応法: 3-down 1-up (収束点 79.4%)
    """
    def __init__(self, frequency=1000, duration_ms=500, start_db=40.0):
        self.frequency = frequency
        self.duration_ms = duration_ms
        self.staircase = ThreeDownOneUpStaircase(start_level=start_db)
        
        # 試行ごとの状態
        self.current_signal_interval = 0 # 1 or 2
        
    def next_trial(self, calibration_instance):
        """
        次の試行の刺激ペア（区間1, 区間2）を生成して返す
        
        Returns:
            (interval1_waveform, interval2_waveform)
            各波形はステレオ (samples, 2)
        """
        level = self.staircase.get_current_level()
        
        # 刺激オブジェクト生成
        signal_stim = PureToneStimulus(self.frequency, self.duration_ms, level)
        silent_stim = SilentStimulus(self.duration_ms)
        
        # 波形生成 (キャリブレーション適用)
        calc_tone = lambda db: calibration_instance.db_to_amplitude(db)
        
        sig_wave = signal_stim.generate(calc_tone)  # (samples,)
        sil_wave = silent_stim.generate()           # (samples,)
        
        # モノーラル（左耳）での提示を想定してステレオ化
        sig_stereo = np.zeros((len(sig_wave), 2), dtype=np.float32)
        sig_stereo[:, 0] = sig_wave
        
        sil_stereo = np.zeros((len(sil_wave), 2), dtype=np.float32)
        
        # ランダムに区間を割り当て
        if random.random() < 0.5:
            self.current_signal_interval = 1
            return (sig_stereo, sil_stereo)
        else:
            self.current_signal_interval = 2
            return (sil_stereo, sig_stereo)

    def register_response(self, user_choice_interval):
        """
        被験者の回答 (1 or 2) を受け取り、正誤判定して適応法を更新
        """
        is_correct = (user_choice_interval == self.current_signal_interval)
        self.staircase.update(is_correct)
        return is_correct

    def is_finished(self):
        return self.staircase.finished

    def get_threshold_result(self):
        """測定された閾値 (dB SPL相当) を返す"""
        return self.staircase.get_threshold()


class PulsationThresholdExperiment:
    """
    脈動閾値実験クラス
    
    独立変数: プローブ周波数
    従属変数: プローブ信号レベル
    マスカー: 固定 (White noise)
    
    ★ Sensation Level (SL) 対応:
    reference_threshold_db を受け取り、ユーザー指定の 'dB SL' を
    実際の出力レベル 'dB SPL(デジタル)' に変換して使用する。
    """
    def __init__(self, signal_freq, reference_threshold_db=0.0, initial_sl_db=70.0):
        self.signal_freq = signal_freq
        self.reference_threshold_db = reference_threshold_db # 0 dB SL に相当するSPL
        
        # マスカーパラメータ（固定）
        self.masker_n0 = 36
        self.masker_cutoff = 1100
        self.masker_stop = 1150
        
        # 適応法トラックの初期化 (SL単位)
        # 閾値上 70dB SL から開始
        self.track1 = AdaptiveStaircase(target_percent=70.7, start_level=initial_sl_db)
        self.track2 = AdaptiveStaircase(target_percent=29.3, start_level=initial_sl_db - 10)
        
        self.active_track = None
        self.current_track_idx = 0

    def _sl_to_system_db(self, sl_db):
        """SL (Sensation Level) -> System dB SPL 変換"""
        return self.reference_threshold_db + sl_db

    def next_trial(self):
        self.current_track_idx = random.choice([1, 2])
        if self.current_track_idx == 1:
            self.active_track = self.track1
        else:
            self.active_track = self.track2
            
        current_sl_level = self.active_track.get_current_level()
        actual_signal_level = self._sl_to_system_db(current_sl_level)
        
        sequence = PulsationSequence(
            signal_freq=self.signal_freq,
            signal_level=actual_signal_level,
            masker_n0=self.masker_n0,
            masker_cutoff=self.masker_cutoff,
            masker_stop=self.masker_stop
        )
        return sequence

    def register_response(self, response_is_continuous):
        if self.active_track:
            self.active_track.update(response_is_continuous)

    def is_finished(self):
        return self.track1.finished and self.track2.finished