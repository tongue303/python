import sys
import time
import sounddevice as sd
from core.experiment import AbsoluteThresholdExperiment
from utils.audio import AudioPlayer, Calibration

def run_absolute_threshold_experiment(player, calib):
    """可聴閾値測定セッションの実行"""
    
    print("\n" + "="*60)
    print("Pre-Experiment: Absolute Threshold Measurement (2IFC)")
    print("="*60)
    print("Instruction:")
    print("  Two sound intervals will be played with a gap in between.")
    print("  Only ONE interval contains a tone. The other is silent.")
    print("  Type '1' if the tone was in the 1st interval.")
    print("  Type '2' if the tone was in the 2nd interval.")
    print("-" * 60)
    
    input("Press Enter to start calibration/measurement...")
    print("Starting in 2 seconds...")
    time.sleep(2)

    # 実験設定: 1000Hz, 開始レベル40dB SPL (聞こえやすいレベルから開始)
    exp = AbsoluteThresholdExperiment(frequency=1000, duration_ms=500, start_db=40.0)
    
    trial_count = 1
    
    while not exp.is_finished():
        print(f"\n--- Trial {trial_count} ---")
        
        # 1. 刺激生成 (信号区間と無音区間のペアを取得)
        interval1, interval2 = exp.next_trial(calib)
        
        # 2. 再生
        player.play_2ifc_sequence(interval1, interval2, gap_ms=500)
        
        # 3. 回答受付
        while True:
            try:
                user_input = input("Which interval contained the tone? (1/2): ").strip()
                if user_input in ['1', '2']:
                    choice = int(user_input)
                    break
                else:
                    print("Invalid input. Please enter '1' or '2'.")
            except ValueError:
                print("Invalid input.")
        
        # 4. 判定と適応法の更新
        is_correct = exp.register_response(choice)
        
        # フィードバック表示（本番では消すことも多いが、動作確認用に表示）
        if is_correct:
            print("  >> Correct!")
        else:
            print("  >> Incorrect.")
            
        trial_count += 1

    # 最終結果の取得
    threshold = exp.get_threshold_result()
    print("\n" + "="*60)
    print(f"Measurement Finished!")
    print(f"Estimated Absolute Threshold: {threshold:.2f} dB SPL")
    print("This value will be used as 0 dB SL for the main experiment.")
    print("="*60)
    
    return threshold

def main():
    print("--- Pulsation Threshold Experiment System ---")
    
    # 1. オーディオデバイス確認
    try:
        device_info = sd.query_devices(kind='output')
        print(f"Using Audio Device: {device_info['name']}")
    except Exception as e:
        print("Error: Could not query audio devices.")
        print(f"Details: {e}")
        print("Please ensure 'sounddevice' is installed (pip install sounddevice)")
        return

    # 2. 初期化
    player = AudioPlayer(fs=50000)
    # PC環境に合わせて最大音圧レベル(dB SPL)を仮定して設定
    # 実際には騒音計で「フルスケール正弦波を再生したときの音圧」を測って設定する
    calib = Calibration(max_spl_db=100.0) 
    
    # 3. 可聴閾値測定の実行確認
    print("\nDo you want to run the Absolute Threshold Measurement?")
    print("If 'n', a default value (0 dB SPL) will be used for testing.")
    user_input = input("Run measurement? (y/n): ").strip().lower()
    
    abs_threshold = 0.0
    if user_input == 'y':
        try:
            abs_threshold = run_absolute_threshold_experiment(player, calib)
        except KeyboardInterrupt:
            print("\nExperiment interrupted by user.")
            sys.exit(0)
    else:
        print("Skipping measurement. Using default threshold: 10.0 dB SPL")
        abs_threshold = 10.0
        
    # 4. 本実験への移行 (プレースホルダー)
    print("\n" + "-"*60)
    print("Ready for Main Experiment (Pulsation Threshold)")
    print(f"Reference Level (0 dB SL) set to: {abs_threshold:.2f} dB SPL")
    print("-"*60)
    
    # ここで PulsationThresholdExperiment を開始するコードを追加可能
    # exp_main = PulsationThresholdExperiment(signal_freq=1000, reference_threshold_db=abs_threshold)
    # ...

if __name__ == "__main__":
    main()