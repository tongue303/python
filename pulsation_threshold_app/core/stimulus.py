import numpy as np

# 論文に基づく定数 [cite: 71, 76, 77, 82]
SAMPLING_RATE = 50000        # 50 kHz [cite: 82]
RAMP_MS = 20                # 20 ms raised-cosine 
OVERLAP_MS = 30             # 30 ms overlap 
LONG_SIGNAL_MS = 540        # 開始/終了シグナルの全持続時間 [cite: 76]
SHORT_SEGMENT_MS = 240      # 中間セグメント(マスカー/シグナル)の全持続時間 [cite: 76]

class PureToneStimulus:
    """20msのraised-cosine rampを持つ正弦波刺激の生成 """
    def __init__(self, frequency, duration_ms, level_db, fs=SAMPLING_RATE):
        self.frequency = frequency
        self.duration_ms = duration_ms
        self.level_db = level_db
        self.fs = fs

    def generate(self):
        """振幅1.0をピークとする波形を生成（レベル調整は後段で行う）"""
        t = np.arange(int(self.fs * self.duration_ms / 1000)) / self.fs
        waveform = np.sin(2 * np.pi * self.frequency * t)
        
        # Rampの作成 (20ms) 
        ramp_samples = int(self.fs * RAMP_MS / 1000)
        # sin^2を用いたraised-cosine ramp
        ramp_up = np.sin(np.pi * np.arange(ramp_samples) / (2 * ramp_samples))**2
        ramp_down = ramp_up[::-1]
        
        # 包絡線の適用
        envelope = np.ones_like(waveform)
        envelope[:ramp_samples] = ramp_up
        envelope[-ramp_samples:] = ramp_down
        
        return waveform * envelope

class PulsationSequence:
    """図1の時系列構造を合成するクラス [cite: 68, 76, 77]"""
    def __init__(self, signal_freq, masker_freq, signal_level, masker_level):
        # 刺激オブジェクトの作成
        self.sig_long = PureToneStimulus(signal_freq, LONG_SIGNAL_MS, signal_level)
        self.sig_short = PureToneStimulus(signal_freq, SHORT_SEGMENT_MS, signal_level)
        self.masker = PureToneStimulus(masker_freq, SHORT_SEGMENT_MS, masker_level)

    def create_sequence(self):
        """
        [Sig(L)] -> [M] -> [Sig(S)] -> [M] -> [Sig(S)] -> [M] -> [Sig(L)]
        各刺激は30msずつオーバーラップさせる [cite: 76, 77]
        """
        # 各要素の生成
        s_l = self.sig_long.generate()
        s_s = self.sig_short.generate()
        m = self.masker.generate()
        
        # シーケンス順序: Sig(L), Masker, Sig(S), Masker, Sig(S), Masker, Sig(L)
        segments = [s_l, m, s_s, m, s_s, m, s_l]
        overlap_samples = int(SAMPLING_RATE * OVERLAP_MS / 1000)
        
        # 全体長の計算 (各セグメントを30ms重ねる)
        total_samples = sum(len(seg) for seg in segments) - (len(segments) - 1) * overlap_samples
        
        # ステレオ波形の初期化 (0: 左/シグナル, 1: 右/マスカー兼用)
        # 論文ではマスカーはセンター(両耳)、シグナルはサイド(片耳) 
        combined = np.zeros((total_samples, 2))
        
        current_idx = 0
        for i, seg in enumerate(segments):
            end_idx = current_idx + len(seg)
            
            # マスカー（インデックス 1, 3, 5）はダイオティック（両耳同一） 
            if i % 2 != 0: 
                combined[current_idx:end_idx, 0] += seg  # 左
                combined[current_idx:end_idx, 1] += seg  # 右
            # シグナル（インデックス 0, 2, 4, 6）はモノーラル（片耳） 
            else:
                combined[current_idx:end_idx, 0] += seg  # 左のみ
            
            current_idx = end_idx - overlap_samples
            
        return combined