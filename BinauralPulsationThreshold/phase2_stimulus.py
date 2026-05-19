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
    low  = center_freq / 2
    high = center_freq * 2
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
    M-T-M-T-M-T-M の交番刺激（7区間）を合成する。

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

    # マスカーの全体レベルを帯域幅から逆算 (±1オクターブ: fc/2 ～ 2fc)
    # BW = f_high - f_low = 2*fc - fc/2 = 1.5 * fc
    bandwidth = 1.5 * test_freq
    overall_masker_db = masker_spectrum_level_db + 10 * np.log10(bandwidth)

    # テスト信号は1試行内で同一波形を使い回す
    test_seg = generate_test_signal(test_level_db, test_itd_seconds, config.TEST_DURATION, test_freq, mod_freq, mod_type)

    # 区間長
    seg_n = test_seg.shape[0]

    # 出力バッファ: 7区間 - (7-1)×クロスフェード
    total_n = seg_n * 7 - cf_n * 6
    out = np.zeros((total_n, 2), dtype=np.float64)

    fade_out = np.linspace(1.0, 0.0, cf_n).reshape(-1, 1)
    fade_in  = np.linspace(0.0, 1.0, cf_n).reshape(-1, 1)

    pos = 0
    # パターン: M T M T M T M (合計7セグメント)
    for i in range(7):
        is_masker = (i % 2 == 0)
        
        if is_masker:
            # マスカーは各バーストで独立したノイズを生成 (Running Noise化)
            seg = generate_bandpass_noise(overall_masker_db, test_freq, masker_itd_sec, config.MASKER_DURATION)
        else:
            seg = test_seg

        if i == 0:
            # 最初の区間
            out[pos : pos + seg_n] += seg
        else:
            # クロスフェード処理
            out[pos : pos + cf_n] *= fade_out
            out[pos : pos + cf_n] += seg[:cf_n] * fade_in
            out[pos + cf_n : pos + seg_n] += seg[cf_n:]

        pos += seg_n - cf_n

    return out.astype(np.float64)


# ────────────────────────────────────────────
# 波形検証用スクリプト（単体実行時のみ）
# ────────────────────────────────────────────

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    sr        = config.SAMPLE_RATE
    masker_spectrum_db = -50.0  # dB/Hz
    test_db   = -40.0
    itd_us    = 400e-6   # 400 us ITD
    test_freq = 4000.0   # Hz  (>= 1500 Hz to activate modulation)
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
    plt.show()
