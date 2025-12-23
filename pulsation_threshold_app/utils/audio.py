class AudioPlayer:
    """音声再生と空間制御 [cite: 72, 83]"""
    def play(self, sequence_waveform):
        """
        マスカーはダイオティック（両耳）、
        シグナルはモノーラル（片耳）で提示 [cite: 72]
        """
        # TODO: sounddevice 等を用いた再生処理
        pass

class Calibration:
    """dB SPL とデジタル振幅の変換管理 [cite: 81]"""
    def __init__(self):
        # 基準となる音圧レベル設定
        pass