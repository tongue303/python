import numpy as np
from scipy import signal

# 論文に基づく定数
SAMPLING_RATE = 50000        # 50 kHz
RAMP_MS = 20                 # 20 ms raised-cosine 
OVERLAP_MS = 30              # 30 ms overlap 
LONG_SIGNAL_MS = 540         # 開始/終了シグナルの全持続時間
SHORT_SEGMENT_MS = 240       # 中間セグメントの全持続時間

class StimulusBase:
    """刺激生成の基底クラス"""
    def __init__(self, duration_ms, level_db, fs=SAMPLING_RATE):
        self.duration_ms = duration_ms
        self.level_db = level_db
        self.fs = fs

    def apply_ramp_and_envelope(self, waveform):
        """Raised-cosine rampの適用"""
        ramp_samples = int(self.fs * RAMP_MS / 1000)
        ramp = np.sin(np.pi * np.arange(ramp_samples) / (2 * ramp_samples))**2
        
        envelope = np.ones_like(waveform)
        if len(envelope) >= 2 * ramp_samples:
            envelope[:ramp_samples] = ramp
            envelope[-ramp_samples:] = ramp[::-1]
            
        return waveform * envelope

class PureToneStimulus(StimulusBase):
    """正弦波刺激"""
    def __init__(self, frequency, duration_ms, level_db, fs=SAMPLING_RATE):
        super().__init__(duration_ms, level_db, fs)
        self.frequency = frequency

    def generate(self, calibration_func=None):
        num_samples = int(self.fs * self.duration_ms / 1000)
        t = np.arange(num_samples) / self.fs
        waveform = np.sin(2 * np.pi * self.frequency * t)
        
        # 振幅調整
        if calibration_func:
            linear_amp = calibration_func(self.level_db)
            waveform = waveform * linear_amp
        
        return self.apply_ramp_and_envelope(waveform)

class SilentStimulus(StimulusBase):
    """無音刺激 (可聴閾値実験の信号なし区間用)"""
    def __init__(self, duration_ms, fs=SAMPLING_RATE):
        super().__init__(duration_ms, -999, fs)

    def generate(self, calibration_func=None):
        num_samples = int(self.fs * self.duration_ms / 1000)
        return np.zeros(num_samples, dtype=np.float32)

class LowPassNoiseStimulus(StimulusBase):
    """急峻なローパスフィルタを適用したホワイトノイズ"""
    def __init__(self, spectral_level_n0, cutoff_freq, stop_freq, duration_ms, fs=SAMPLING_RATE):
        super().__init__(duration_ms, spectral_level_n0, fs)
        self.cutoff_freq = cutoff_freq
        self.stop_freq = stop_freq
        self.n0 = spectral_level_n0

    def generate(self, calibration_func):
        num_samples = int(self.fs * self.duration_ms / 1000)
        
        # ホワイトノイズ生成
        white_noise = np.random.normal(0, 1, num_samples)
        
        # フィルタ設計
        nyq = 0.5 * self.fs
        wp = self.cutoff_freq / nyq
        ws = self.stop_freq / nyq
        gpass = 3.0  # -3dB
        gstop = 20.0 # -20dB
        
        b, a = signal.iirdesign(wp, ws, gpass, gstop, ftype='ellip')
        
        # フィルタ適用
        filtered_noise = signal.lfilter(b, a, white_noise)
        
        # レベル調整
        if calibration_func:
            target_amp = calibration_func(self.n0) # noise用メソッド呼出し想定
            current_rms = np.sqrt(np.mean(filtered_noise**2))
            if current_rms > 0:
                filtered_noise = (filtered_noise / current_rms) * target_amp
            
        return self.apply_ramp_and_envelope(filtered_noise)

class PulsationSequence:
    """本実験用のシーケンス合成クラス"""
    def __init__(self, signal_freq, signal_level, masker_n0=36, masker_cutoff=1100, masker_stop=1150):
        self.sig_long = PureToneStimulus(signal_freq, LONG_SIGNAL_MS, signal_level)
        self.sig_short = PureToneStimulus(signal_freq, SHORT_SEGMENT_MS, signal_level)
        
        self.masker = LowPassNoiseStimulus(
            spectral_level_n0=masker_n0,
            cutoff_freq=masker_cutoff,
            stop_freq=masker_stop,
            duration_ms=SHORT_SEGMENT_MS
        )

    def create_sequence(self, calibration_instance):
        calc_tone = lambda db: calibration_instance.db_to_amplitude(db)
        calc_noise = lambda db: calibration_instance.n0_to_amplitude(db)
        
        s_l = self.sig_long.generate(calc_tone)
        s_s = self.sig_short.generate(calc_tone)
        m = self.masker.generate(calc_noise) # n0指定時はここを調整
        
        segments = [s_l, m, s_s, m, s_s, m, s_l]
        overlap_samples = int(SAMPLING_RATE * OVERLAP_MS / 1000)
        
        total_samples = sum(len(seg) for seg in segments) - (len(segments) - 1) * overlap_samples
        combined = np.zeros((total_samples, 2), dtype=np.float32)
        
        current_idx = 0
        for i, seg in enumerate(segments):
            seg_len = len(seg)
            end_idx = current_idx + seg_len
            
            # マスカー (i=奇数): 両耳
            if i % 2 != 0: 
                combined[current_idx:end_idx, 0] += seg
                combined[current_idx:end_idx, 1] += seg
            # シグナル (i=偶数): 片耳 (Left)
            else:
                combined[current_idx:end_idx, 0] += seg
            
            current_idx = end_idx - overlap_samples
            
        return combined