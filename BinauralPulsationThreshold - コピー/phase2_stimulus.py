"""
phase2_stimulus.py
==================
Phase 2: 刺激音生成モジュール

提供する関数:
  - generate_pink_noise(level_db_fs, duration)
  - generate_test_signal(level_db_fs, itd_seconds, duration)
  - build_alternating_stimulus(masker_level_db, test_level_db, itd_seconds)
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
# ピンクノイズ生成
# ────────────────────────────────────────────

def generate_pink_noise(level_db_fs: float, duration: float = config.MASKER_DURATION) -> np.ndarray:
    """
    ピンクノイズ（1/f）をモノラルで生成する。

    FFTによる 1/√f フィルタリングで生成。
    ITD=0 のため左右同一の波形をステレオ化して返す。

    Parameters
    ----------
    level_db_fs : float
        提示レベル (dB FS)。
    duration : float
        長さ（秒）。

    Returns
    -------
    np.ndarray
        shape (n_samples, 2) の float32 ステレオ配列。
    """
    sr = config.SAMPLE_RATE
    n = int(sr * duration)

    # ホワイトノイズ → FFT → 1/√f フィルタ → IFFT
    white = np.random.randn(n)
    fft_w = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n, d=1.0 / sr)
    freqs[0] = 1.0  # DC成分はゼロ除算を避けるため 1.0 にする
    fft_pink = fft_w / np.sqrt(freqs)
    fft_pink[0] = 0.0  # DC除去
    pink = np.fft.irfft(fft_pink, n=n)

    # RMS正規化 → レベル適用 → テーパー
    amplitude = _db_to_amplitude(level_db_fs)
    pink = _rms_normalize(pink, target_rms=1.0) * amplitude
    _apply_cosine_ramp(pink, sr, config.RAMP_DURATION)

    stereo = np.column_stack([pink, pink]).astype(np.float32)
    return stereo


# ────────────────────────────────────────────
# テスト信号生成（500Hz + ITD）
# ────────────────────────────────────────────

def generate_test_signal(
    level_db_fs: float,
    itd_seconds: float,
    duration: float = config.TEST_DURATION,
) -> np.ndarray:
    """
    500Hz 正弦波テスト信号を生成する。

    ITDは微細構造（fine structure）の位相差として付与する。
    エンベロープ（立ち上がり・立ち下がり）は左右同一（ITD=0相当）。

    Parameters
    ----------
    level_db_fs : float
        提示レベル (dB FS)。
    itd_seconds : float
        Interaural Time Delay（秒）。正値 → 右チャネルを遅延。
    duration : float
        長さ（秒）。

    Returns
    -------
    np.ndarray
        shape (n_samples, 2) の float32 ステレオ配列。
    """
    sr = config.SAMPLE_RATE
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    amplitude = _db_to_amplitude(level_db_fs)

    # ITDを位相差に変換（500 Hz: 1周期 = 2ms）
    phase_delay_rad = 2 * np.pi * config.TEST_FREQ * itd_seconds

    left = amplitude * np.sin(2 * np.pi * config.TEST_FREQ * t)
    right = amplitude * np.sin(2 * np.pi * config.TEST_FREQ * t - phase_delay_rad)

    # エンベロープテーパー（左右共通）
    ramp_n = int(sr * config.RAMP_DURATION)
    if ramp_n > 0:
        ramp = 0.5 * (1 - np.cos(np.pi * np.arange(ramp_n) / ramp_n))
        left[:ramp_n] *= ramp;  left[-ramp_n:] *= ramp[::-1]
        right[:ramp_n] *= ramp; right[-ramp_n:] *= ramp[::-1]

    stereo = np.column_stack([left, right]).astype(np.float32)
    return stereo


# ────────────────────────────────────────────
# 交番刺激合成 M-T-M-T-M-T-M
# ────────────────────────────────────────────

def build_alternating_stimulus(
    masker_level_db: float,
    test_level_db: float,
    itd_seconds: float,
) -> np.ndarray:
    """
    M-T-M-T-M-T-M の交番刺激（7区間）を合成する。

    隣接区間は CROSSFADE_DURATION 秒のクロスフェードでつなぐ。
    全体の長さは約 1035 ms。

    Parameters
    ----------
    masker_level_db : float
        マスカー提示レベル (dB FS)。
    test_level_db : float
        テスト信号提示レベル (dB FS)。
    itd_seconds : float
        テスト信号の ITD（秒）。

    Returns
    -------
    np.ndarray
        shape (n_total, 2) の float32 ステレオ配列。
    """
    sr = config.SAMPLE_RATE
    cf_n = int(sr * config.CROSSFADE_DURATION)  # クロスフェードサンプル数

    # 各区間を生成
    masker_seg = generate_pink_noise(masker_level_db, config.MASKER_DURATION)
    test_seg = generate_test_signal(test_level_db, itd_seconds, config.TEST_DURATION)

    # パターン: M T M T M T M
    segments = [
        masker_seg.copy(),
        test_seg.copy(),
        masker_seg.copy(),
        test_seg.copy(),
        masker_seg.copy(),
        test_seg.copy(),
        masker_seg.copy(),
    ]

    # 区間長
    seg_n = segments[0].shape[0]

    # 出力バッファ: 7区間 - (7-1)×クロスフェード
    total_n = seg_n * 7 - cf_n * 6
    out = np.zeros((total_n, 2), dtype=np.float64)

    fade_out = np.linspace(1.0, 0.0, cf_n).reshape(-1, 1)
    fade_in  = np.linspace(0.0, 1.0, cf_n).reshape(-1, 1)

    pos = 0
    for i, seg in enumerate(segments):
        if i == 0:
            # 最初の区間: 全て書き込む（末尾のクロスフェード部分も含む）
            out[pos: pos + seg_n] += seg
        else:
            # ① 前区間の末尾（クロスフェード領域）をフェードアウト
            #    out[pos : pos+cf_n] には前区間の末尾 cf_n サンプルが入っている
            out[pos: pos + cf_n] *= fade_out

            # ② 現区間の先頭をフェードインしながら加算
            out[pos: pos + cf_n] += seg[:cf_n] * fade_in

            # ③ クロスフェード後の残り本体を加算
            out[pos + cf_n: pos + seg_n] += seg[cf_n:]

        pos += seg_n - cf_n  # 次区間の開始位置（クロスフェード分だけ手前）

    return out.astype(np.float32)


# ────────────────────────────────────────────
# 波形検証用スクリプト（単体実行時のみ）
# ────────────────────────────────────────────

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    sr = config.SAMPLE_RATE
    masker_db = -20.0
    test_db   = -40.0
    itd_us    = 400e-6  # 400 µs

    stim = build_alternating_stimulus(masker_db, test_db, itd_us)
    t_axis = np.arange(stim.shape[0]) / sr * 1000  # ms

    fig, axes = plt.subplots(2, 1, figsize=(12, 5), sharex=True)
    axes[0].plot(t_axis, stim[:, 0], lw=0.5, label="Left")
    axes[0].set_ylabel("Amplitude"); axes[0].legend(); axes[0].set_title("交番刺激 (Left ch)")
    axes[1].plot(t_axis, stim[:, 1], lw=0.5, color="orange", label="Right")
    axes[1].set_xlabel("Time (ms)"); axes[1].set_ylabel("Amplitude")
    axes[1].legend(); axes[1].set_title("交番刺激 (Right ch)")
    plt.tight_layout()
    plt.savefig("stimulus_waveform.png", dpi=150)
    print(f"波形を stimulus_waveform.png に保存しました（{stim.shape[0]/sr*1000:.1f} ms）")
    plt.show()
