from .stimulus import PureToneStimulus
from .adaptive import AdaptiveStaircase

class AbsoluteThresholdExperiment:
    """可聴閾値（Absolute Threshold）の測定 [cite: 116]"""
    def __init__(self, subject_id, frequency):
        # TODO: 3-down 1-up 等の適応法を用いた閾値測定 [cite: 122]
        pass

class PulsationThresholdExperiment:
    """メインの脈動閾値実験 [cite: 7, 49]"""
    def __init__(self, signal_freq, signal_level_db):
        self.signal_freq = signal_freq
        self.masker_freq = signal_freq * 0.6  # マスカーはシグナルの0.6倍 [cite: 8, 80]
        self.track1 = AdaptiveStaircase(70.7)
        self.track2 = AdaptiveStaircase(29.3)

    def next_trial(self):
        """Track 1か2をランダムに選択して試行を準備"""
        pass