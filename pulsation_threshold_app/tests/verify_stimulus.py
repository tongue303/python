# tests/verify_stimulus.py
import sys
import os
import matplotlib.pyplot as plt
import numpy as np

# 親ディレクトリをパスに追加して core パッケージを読み込めるようにする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.stimulus import PulsationSequence

def plot_verification(sequence_waveform, fs=50000):
    t = np.arange(len(sequence_waveform)) / fs
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    plt.subplots_adjust(hspace=0.4)

    # --- 1. 全体像のプロット ---
    ax1.plot(t, sequence_waveform[:, 0], label='Left (Signal + Masker)', alpha=0.7)
    ax1.plot(t, sequence_waveform[:, 1], label='Right (Masker only)', alpha=0.5)
    ax1.set_title("Stimulus Sequence Overview (Entire Duration)")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Amplitude")
    ax1.legend(loc='upper right')
    ax1.grid(True)

    # --- 2. 最初の遷移部分(SigL -> Masker)の拡大プロット ---
    # 最初のSigLが540ms、オーバーラップが30msなので、510ms付近を拡大
    zoom_start, zoom_end = 0.50, 0.58  # 500msから580ms付近
    mask = (t >= zoom_start) & (t <= zoom_end)
    
    ax2.plot(t[mask], sequence_waveform[mask, 0], label='Left Channel', alpha=0.8)
    ax2.plot(t[mask], sequence_waveform[mask, 1], label='Right Channel', alpha=0.8)
    
    # 30msのオーバーラップ区間を強調
    ax2.axvspan(0.51, 0.54, color='yellow', alpha=0.2, label='30ms Overlap Zone')
    
    ax2.set_title("Zoom-in: Signal (L) to Masker (Diotic) Transition")
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Amplitude")
    ax2.legend(loc='upper right')
    ax2.grid(True)

    plt.show()

# テスト実行
if __name__ == "__main__":
    # 実験設定: シグナル1000Hz, マスカー600Hz
    # レベルは一旦 1.0 (最大) として合成
    creator = PulsationSequence(1000, 600, 1.0, 1.0)
    waveform = creator.create_sequence()
    
    print(f"Waveform shape: {waveform.shape}") # (サンプル数, 2)
    plot_verification(waveform)