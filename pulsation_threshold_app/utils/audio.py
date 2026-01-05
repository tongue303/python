import numpy as np
import sounddevice as sd
import time

class AudioPlayer:
    """音声再生制御クラス (sounddevice使用)"""
    def __init__(self, fs=50000):
        self.fs = fs

    def play(self, waveform):
        """
        波形を再生する (ブロッキング再生: 再生が終わるまで待機)
        waveform: (samples, channels) のnumpy配列
        """
        # sounddeviceはfloat32推奨
        if waveform.dtype != np.float32:
            waveform = waveform.astype(np.float32)
            
        try:
            sd.play(waveform, self.fs, blocking=True)
        except Exception as e:
            print(f"Audio Playback Error: {e}")

    def play_2ifc_sequence(self, interval1, interval2, gap_ms=500):
        """
        2IFC課題用に2つの刺激を間隔を空けて再生する
        """
        print("  Interval 1...", end="", flush=True)
        self.play(interval1)
        print(" Done.")
        
        # ギャップ (無音待機)
        time.sleep(gap_ms / 1000.0)
        
        print("  Interval 2...", end="", flush=True)
        self.play(interval2)
        print(" Done.")

class Calibration:
    """
    dB SPL / dB/Hz とデジタル振幅の変換管理
    ※ 実際の実験では騒音計を用いた実測値に基づく補正が必要です。
    """
    def __init__(self, max_spl_db=100.0):
        # システムの最大出力（デジタル振幅1.0のときのSPL）
        # ご自身の環境（PC音量、ヘッドホン）に合わせて調整してください。
        # 例: PCの音量を最大にしたとき、フルスケール正弦波が100dB SPL出ると仮定。
        self.max_spl_db = max_spl_db

    def db_to_amplitude(self, target_db):
        """dB SPL を リニア振幅 (0.0 - 1.0) に変換"""
        # target_db = 20 * log10(amp) + max_spl
        # amp = 10 ** ((target_db - max_spl) / 20)
        
        # 安全のため最大出力を超える要求が来たらクリップする
        if target_db > self.max_spl_db:
            print(f"Warning: Requested {target_db} dB SPL exceeds max system output. Clipping.")
            return 1.0
            
        amp = 10 ** ((target_db - self.max_spl_db) / 20.0)
        return amp

    def n0_to_amplitude(self, target_n0):
        """
        スペクトル密度レベル N0 (dB/Hz) を、デジタルノイズのRMS振幅に変換
        
        デジタルホワイトノイズの総パワーは帯域幅（Nyquist）に依存するため、
        N0 (1Hzあたりのパワー) から必要な総パワーを逆算して振幅を求める。
        """
        # サンプリング周波数 fs=50000 -> Nyquist=25000 Hz
        fs = 50000 
        nyquist = fs / 2
        
        # Total Power (dB) = N0 + 10 * log10(Bandwidth)
        total_power_db = target_n0 + 10 * np.log10(nyquist)
        
        return self.db_to_amplitude(total_power_db)