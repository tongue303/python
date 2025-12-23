from core.experiment import AbsoluteThresholdExperiment, PulsationThresholdExperiment
from utils.audio import Calibration

def main():
    print("--- Plack and Oxenham (2000) 実験プログラム ---")
    
    # 1. キャリブレーション設定
    calib = Calibration()
    
    # 2. 事前測定：可聴閾値の取得 [cite: 116]
    # abs_threshold = AbsoluteThresholdExperiment(...)
    
    # 3. 本実験：脈動閾値の測定 [cite: 7]
    # exp = PulsationThresholdExperiment(...)
    
    print("プログラムのスケルトンが準備できました。")

if __name__ == "__main__":
    main()