# -*- coding: utf-8 -*-
"""
phase2_stimulus.py
==================
Phase 2: 刺激音生成モジュール

提供する関数:
  - generate_bandpass_noise(level_db_fs, center_freq, itd_seconds, duration)
      帯域通過ノイズ（通過帯域: center_freq/2 ～ center_freq×2、±1 オクターブ対称）
  - generate_test_signal(level_db_fs, itd_seconds, duration, ...)
      テスト信号（純音 / SAM / Transposed）
  - build_alternating_stimulus(masker_level_db, test_level_db, test_itd_seconds, ...)
      M-T-M-T-M-T-M 交番刺激の合成
"""

import numpy as np
import config


# ────────────────────────────────────────────
# 内部ユーティリティ
# ────────────────────────────────────────────

def _apply_cosine_ramp(wave: np.ndarray, sr: int, ramp_sec: float) -> np.ndarray:
    """配列の両端にコサインテーパーを適用する（in-place）。"""
    ramp_n = int(sr * ramp_sec)
    if ramp_n == 0:
        return wave
    ramp = 0.5 * (1 - np.cos(np.pi * np.arange(ramp_n) / ramp_n))
    wave[:ramp_n] *= ramp
    wave[-ramp_n:] *= ramp[::-1]
    return wave


def _rms_normalize(wave: np.ndarray, target_rms: float = 1.0) -> np.ndarray:
    """RMS正規化。"""
    rms = np.sqrt(np.mean(wave ** 2))
    if rms < 1e-10:
        return wave
    return wave * (target_rms / rms)


def _db_to_amplitude(level_db_fs: float) -> float:
    """dB FS → 振幅変換（0 dB FS = 振幅 1.0）。"""
    return 10 ** (level_db_fs / 20.0)


# ────────────────────────────────────────────
# バンドパスノイズ生成
# ────────────────────────────────────────────

def generate_bandpass_noise(
    level_db_fs: float,
    center_freq: float,
    itd_seconds: float = 0.0,
    duration: float = config.MASKER_DURATION,
) -> np.ndarray:
    """
    帯域通過ホワイトノイズを生成し、ITD（時間遅延）を付与してステレオ化する。

    通過帯域: center_freq / 2 ～ center_freq × 2（±1 オクターブ対称）
    バタワース 4 次バンドパスフィルタを適用する。

    Parameters
    ----------
    level_db_fs : float
        提示レベル (dB FS)。
    center_freq : float
        マスカーの中心周波数 (Hz)。テスト信号と同じ周波数を指定する。
    itd_seconds : float
        Interaural Time Delay（秒）。正値 → 右チャネルを遅延。
    duration : float
        長さ（秒）。

    Returns
    -------
    np.ndarray
        shape (n_samples, 2) の float64 ステレオ配列。
    """
    from scipy.signal import butter, sosfilt

    sr = config.SAMPLE_RATE
    base_n = int(sr * duration)
    shift_n = int(np.round(abs(itd_seconds) * sr))
    total_n = base_n + shift_n

    # 通過帯域: fc/2 ～ fc×2（±1 オクターブ対称）
    low  = center_freq / np.sqrt(2)
    high = center_freq * np.sqrt(2)
    # バタワースフィルタの有効範囲にクランプ（DC・ナイキストを避ける）
    low  = max(low,  20.0)
    high = min(high, sr / 2.0 - 1.0)

    # 4次バタワースバンドパスフィルタ
    sos = butter(4, [low, high], btype='bandpass', fs=sr, output='sos')

    # ホワイトノイズ生成 → フィルタ適用
    white    = np.random.randn(total_n)
    filtered = sosfilt(sos, white)

    # ITD分割の前に全体をRMS正規化 → L/R で同一の正規化係数を使うことで
    # 毎試行のILD（両耳レベル差）の変動を防ぐ
    amplitude = _db_to_amplitude(level_db_fs)
    filtered  = _rms_normalize(filtered, target_rms=1.0) * amplitude

    # 左右の切り出しにより時間遅延(ITD)を実現
    left  = np.zeros(base_n)
    right = np.zeros(base_n)
    if itd_seconds >= 0:
        right[:] = filtered[:base_n]
        left[:]  = filtered[shift_n : shift_n + base_n]
    else:
        left[:]  = filtered[:base_n]
        right[:] = filtered[shift_n : shift_n + base_n]

    _apply_cosine_ramp(left,  sr, config.RAMP_DURATION)
    _apply_cosine_ramp(right, sr, config.RAMP_DURATION)

    return np.column_stack([left, right]).astype(np.float64)


# ────────────────────────────────────────────
# テスト信号生成（500Hz + ITD）
# ────────────────────────────────────────────

def generate_test_signal(
    level_db_fs: float,
    itd_seconds: float,
    duration: float = config.TEST_DURATION,
    test_freq: float = config.TEST_FREQ,
    mod_freq: float = config.MOD_FREQ,
    mod_type: str = "None",
) -> np.ndarray:
    """
    テスト信号（純音、SAM、Transposed）を生成しITDを付与する。
    1.5kHz以上かつmod_typeが設定されていれば変調を行う。

    Parameters
    ----------
    level_db_fs : float
        提示レベル (dB FS)。
    itd_seconds : float
        Interaural Time Delay（秒）。正値 → 右チャネルを遅延。
    duration : float
        長さ（秒）。
    test_freq : float
        テスト周波数 (Hz)
    mod_freq : float
        変調周波数 (Hz)
    mod_type : str
        "None", "SAM", "Transposed" のいずれか

    Returns
    -------
    np.ndarray
        shape (n_samples, 2) の float32 ステレオ配列。
    """
    sr = config.SAMPLE_RATE
    base_n = int(sr * duration)
    shift_n = int(np.round(abs(itd_seconds) * sr))
    total_n = base_n + shift_n
    
    t = np.linspace(0, total_n / sr, total_n, endpoint=False)
    
    # キャリア成分
    carrier = np.sin(2 * np.pi * test_freq * t)
    
    if test_freq >= 1500.0 and mod_type != "None":
        if mod_type == "SAM":
            # SAM envelope: 1 - cos(2*pi*f_mod*t)
            envelope = 1.0 - np.cos(2 * np.pi * mod_freq * t)
        elif mod_type == "Transposed":
            # Transposed envelope: Half-wave rectified cosine
            envelope = np.maximum(0, np.cos(2 * np.pi * mod_freq * t))
        else:
            envelope = 1.0
        
        signal = carrier * envelope
    else:
        signal = carrier

    # RMSを1.0に合わせた後、振幅を設定
    signal = _rms_normalize(signal, target_rms=1.0)

    left = np.zeros(base_n)
    right = np.zeros(base_n)
    if itd_seconds >= 0:
        right[:] = signal[:base_n]
        left[:] = signal[shift_n : shift_n + base_n]
    else:
        left[:] = signal[:base_n]
        right[:] = signal[shift_n : shift_n + base_n]
        
    amplitude = _db_to_amplitude(level_db_fs)
    left *= amplitude
    right *= amplitude

    # エンベロープテーパー（左右別々に適用）
    _apply_cosine_ramp(left, sr, config.RAMP_DURATION)
    _apply_cosine_ramp(right, sr, config.RAMP_DURATION)

    stereo = np.column_stack([left, right]).astype(np.float64)
    return stereo


# ────────────────────────────────────────────
# 交番刺激合成 M-T-M-T-M-T-M
# ────────────────────────────────────────────

def build_alternating_stimulus(
    masker_spectrum_level_db: float,
    test_level_db: float,
    test_itd_seconds: float,
    test_freq: float = config.TEST_FREQ,
    mod_freq: float = config.MOD_FREQ,
    mod_type: str = "None",
    masker_itd_sec: float = 0.0,
) -> np.ndarray:
    """
    T-M-T-M-T-M-T-S の交番刺激（8区間）を合成する。

    隣接区間は CROSSFADE_DURATION 秒のクロスフェードでつなぐ。

    Parameters
    ----------
    masker_spectrum_level_db : float
        マスカーのスペクトルレベル (dB/Hz)。
    test_level_db : float
        テスト信号提示レベル (dB FS)。
    test_itd_seconds : float
        テスト信号の ITD（秒）。

    Returns
    -------
    np.ndarray
        shape (n_total, 2) の float64 ステレオ配列。
    """
    sr = config.SAMPLE_RATE
    cf_n = int(sr * config.CROSSFADE_DURATION)  # クロスフェードサンプル数

    # マスカーの全体レベルを帯域幅から逆算 (fc/sqrt(2) ～ fc*sqrt(2))
    bandwidth = test_freq * np.sqrt(2) - (test_freq / np.sqrt(2))
    overall_masker_db = masker_spectrum_level_db + 10 * np.log10(bandwidth)
    
    # テスト信号は1試行内で同一波形を使い回す
    test_seg = generate_test_signal(test_level_db, test_itd_seconds, config.TEST_DURATION, test_freq, mod_freq, mod_type)

    # 区間長
    seg_n = test_seg.shape[0]

    # セグメント数の計算: N_TEST回のテスト信号 + (N_TEST-1)回のマスカー + 1回の無音 = 2 * N_TEST
    total_segments = 2 * config.N_TEST

    # 出力バッファ: total_segments区間 - (total_segments-1)×クロスフェード
    total_n = seg_n * total_segments - cf_n * (total_segments - 1)
    out = np.zeros((total_n, 2), dtype=np.float64)

    pos = 0
    # パターン: T M T M ... S (合計 total_segments セグメント)
    for i in range(total_segments):
        if i == total_segments - 1:
            # 無音区間 (S)
            seg = np.zeros((seg_n, 2), dtype=np.float64)
        elif i % 2 == 0:
            # T: テスト信号
            seg = test_seg
        else:
            # M: マスカーは各バーストで独立したノイズを生成 (Running Noise化)
            seg = generate_bandpass_noise(overall_masker_db, test_freq, masker_itd_sec, config.MASKER_DURATION)

        # 各セグメントは既にコサインテーパーが適用されているため、単純なオーバーラップ加算でクロスフェードさせる
        out[pos : pos + seg_n] += seg

        pos += seg_n - cf_n

    # クリップ判定（振幅が1.0以上になると音声出力時に波形が歪む）
    if np.max(np.abs(out)) > 0.99:
        raise ValueError(
            "生成された刺激音の振幅がクリップの閾値（1.0）を超えました。\n"
            "config.TARGET_SL を下げるか、PCの出力音量を下げてアンプ側のゲインを上げてください。"
        )

    return out.astype(np.float64)


# ────────────────────────────────────────────
# 波形検証用スクリプト（単体実行時のみ）
# ────────────────────────────────────────────

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    sr        = config.SAMPLE_RATE
    masker_spectrum_db = -50.0  # dB/Hz
    test_db   = -50.0
    itd_us    = 400e-6   # 400 us ITD
    test_freq = 500.0   # Hz  (>= 1500 Hz to activate modulation)
    mod_freq  = config.MOD_FREQ
    mod_type  = "Transposed"    # "None" | "SAM" | "Transposed"

    stim = build_alternating_stimulus(
        masker_spectrum_db, test_db, itd_us,
        test_freq=test_freq,
        mod_freq=mod_freq,
        mod_type=mod_type,
    )
    t_axis = np.arange(stim.shape[0]) / sr * 1000  # ms

    fig, axes = plt.subplots(2, 1, figsize=(12, 5), sharex=True)
    axes[0].plot(t_axis, stim[:, 0], lw=0.5, label="Left")
    axes[0].set_ylabel("Amplitude")
    axes[0].legend()
    axes[0].set_title(f"Alternating Stimulus (Left ch) | {test_freq:.0f} Hz, {mod_type}, ITD={itd_us*1e6:.0f} us")
    axes[1].plot(t_axis, stim[:, 1], lw=0.5, color="orange", label="Right")
    axes[1].set_xlabel("Time (ms)")
    axes[1].set_ylabel("Amplitude")
    axes[1].legend()
    axes[1].set_title("Alternating Stimulus (Right ch)")
    plt.tight_layout()
    plt.savefig("stimulus_waveform.png", dpi=150)
    print(f"Waveform saved to stimulus_waveform.png  ({stim.shape[0]/sr*1000:.1f} ms)")

    # ────────────────────────────────────────────
    # クロスフェードのランプ係数検証
    # ────────────────────────────────────────────
    ramp_n = int(sr * config.RAMP_DURATION)
    if ramp_n > 0:
        fade_in_ramp = 0.5 * (1 - np.cos(np.pi * np.arange(ramp_n) / ramp_n))
        fade_out_ramp = fade_in_ramp[::-1]
        sum_ramp = fade_in_ramp + fade_out_ramp
        
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.plot(fade_in_ramp, label="Fade In Ramp", linestyle="--")
        ax2.plot(fade_out_ramp, label="Fade Out Ramp", linestyle="--")
        ax2.plot(sum_ramp, label="Sum", linewidth=2, color="black")
        ax2.set_title("Cosine Crossfade Ramp Verification")
        ax2.set_xlabel("Samples")
        ax2.set_ylabel("Gain")
        ax2.set_ylim(-0.1, 1.2)
        ax2.legend()
        plt.tight_layout()
        plt.savefig("ramp_verification.png", dpi=150)
        print("Ramp verification saved to ramp_verification.png")
        print(f"Max deviation of sum from 1.0: {np.max(np.abs(sum_ramp - 1.0)):.2e}")

    # ────────────────────────────────────────────
    # マスカーのスペクトル密度(dB/Hz) と テスト信号(dB) の検証
    # ────────────────────────────────────────────
    from scipy.signal import welch

    # PSD推定のため長めの信号を生成
    bw = test_freq * np.sqrt(2) - (test_freq / np.sqrt(2))
    overall_masker_db = masker_spectrum_db + 10 * np.log10(bw)
    long_masker_duration = 2.0
    long_masker = generate_bandpass_noise(overall_masker_db, test_freq, itd_seconds=0.0, duration=long_masker_duration)
    # 純音テスト信号も生成
    long_test = generate_test_signal(test_db, itd_seconds=0.0, duration=long_masker_duration, test_freq=test_freq, mod_freq=mod_freq, mod_type="None")
    
    # 中央の安定した部分を抽出（ランプの影響を除外）
    margin = int(sr * config.RAMP_DURATION) + int(sr * 0.1)
    stable_masker = long_masker[margin:-margin, 0]  # Left chのみ使用
    stable_test = long_test[margin:-margin, 0]

    # Welch法でPSD推定 (nperseg=8192)
    nperseg = 8192*2
    df = sr / nperseg
    f, Pxx_masker = welch(stable_masker, fs=sr, nperseg=nperseg)
    f, Pxx_test = welch(stable_test, fs=sr, nperseg=nperseg)

    # マスカーの平均PSDを計算
    f_low = test_freq / np.sqrt(2)
    f_high = test_freq * np.sqrt(2)
    valid_idx = (f >= f_low) & (f <= f_high)
    mean_psd_linear = np.mean(Pxx_masker[valid_idx])
    measured_spectrum_db = 10 * np.log10(mean_psd_linear)

    # テスト信号（純音）のトータルパワーを計算
    measured_test_power = np.sum(Pxx_test) * df
    measured_test_db = 10 * np.log10(measured_test_power)

    print("\n--- Spectrum Level Verification ---")
    print(f"Target Masker Spectrum Level:   {masker_spectrum_db:.2f} dB/Hz")
    print(f"Measured Masker Spectrum Level: {measured_spectrum_db:.2f} dB/Hz (Error: {measured_spectrum_db - masker_spectrum_db:.2f} dB)")
    
    print("\n--- Test Signal (Tone) Level Verification ---")
    print(f"Target Test Level:              {test_db:.2f} dB")
    print(f"Measured Test Level:            {measured_test_db:.2f} dB (Error: {measured_test_db - test_db:.2f} dB)")

    # グラフの描画
    fig3, ax3 = plt.subplots(figsize=(8, 4))
    
    # マスカープロット
    ax3.plot(f, 10 * np.log10(Pxx_masker + 1e-12), label="Masker PSD", color="blue", lw=1)
    ax3.axhline(masker_spectrum_db, color="red", linestyle="--", label=f"Masker Target: {masker_spectrum_db} dB/Hz")
    
    # テスト信号プロット (パワースペクトル: 密度 × df)
    ax3.plot(f, 10 * np.log10(Pxx_test * df + 1e-12), label="Test Signal (Power, dB)", color="orange", lw=1, alpha=0.8)
    # 純音のパワースペクトルのピーク理論値 = test_db
    ax3.plot(test_freq, test_db, 'ro', label=f"Test Peak Target: {test_db:.1f} dB")
    
    ax3.axvline(f_low, color="green", linestyle=":", label=f"f_low: {f_low:.1f} Hz")
    ax3.axvline(f_high, color="green", linestyle=":", label=f"f_high: {f_high:.1f} Hz")
    
    ax3.set_xlim(max(0, f_low - 1000), min(sr/2, f_high + 1000))
    # Y軸の範囲を純音ピークとマスカー床が入るように調整
    ylim_min = masker_spectrum_db - 20
    ylim_max = max(test_db, masker_spectrum_db) + 15
    ax3.set_ylim(ylim_min, ylim_max)
    
    ax3.set_xlabel("Frequency (Hz)")
    ax3.set_ylabel("Level (dB/Hz for Masker, dB for Tone)")
    ax3.set_title("Masker Spectrum Level & Test Tone Verification")
    ax3.legend(loc='upper right', fontsize='small')
    plt.tight_layout()
    plt.savefig("psd_verification.png", dpi=150)
    print("PSD verification saved to psd_verification.png")

    plt.show()
