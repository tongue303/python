# -*- coding: utf-8 -*-
"""
plot_results.py
===============
パルセーション閾値測定結果のポストプロセス・可視化スクリプト（調整法対応）

機能:
  1. data/ フォルダ内の最新 CSV（または引数指定）を読み込む
  2. ITDごとのパルセーション閾値を折れ線グラフ（または棒グラフ）で描画する
  3. 図を PNG として保存

使い方:
  python plot_results.py                          # data/ 内の最新CSVを自動選択
  python plot_results.py data/P01_xxx.csv         # ファイルを指定
"""

import sys
import os
import glob
import platform
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

import config

# ── OS別 日本語フォント自動選択 ──
_os = platform.system()
if _os == "Windows":
    _font = "Meiryo"
elif _os == "Darwin":  # macOS
    _font = "Hiragino Sans"
else:
    _font = "sans-serif"
plt.rcParams["font.family"] = _font
plt.rcParams["axes.unicode_minus"] = False


# ────────────────────────────────────────────
# CSV 読み込み
# ────────────────────────────────────────────

def load_csv(path: str | None = None) -> tuple[pd.DataFrame, str]:
    """
    CSV を読み込む。path が None なら data/ 内の最新ファイルを使用。
    返り値: (DataFrame, ファイルパス)
    """
    if path is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
        if not files:
            raise FileNotFoundError("data/ フォルダに CSV ファイルが見つかりません。")
        path = files[-1]  # 最新ファイル

    df = pd.read_csv(path)
    
    if "sl_reference_db" in df.columns and "threshold_db" in df.columns:
        # FSベースからSL(1kHz)ベースに校正
        df["threshold_db"] = df["threshold_db"] - df["sl_reference_db"]

    print(f"読み込み: {path}  ({len(df)} 行)")
    return df, path


# ────────────────────────────────────────────
# プロット
# ────────────────────────────────────────────

def plot_all(df: pd.DataFrame, save_prefix: str) -> None:
    """
    ITDごとの閾値を描画・保存する。
    """
    # ITDでソート
    df = df.sort_values(by="itd_us")
    
    itd_list = df["itd_us"].values
    threshold_vals = df["threshold_db"].values
    n_itd = len(itd_list)
    subject = df["subject_id"].iloc[0]
    
    # メタデータ取得（過去のデータ対応付き）
    test_freq = df["test_freq"].iloc[0] if "test_freq" in df.columns else config.TEST_FREQ
    mod_type = df["mod_type"].iloc[0] if "mod_type" in df.columns else "None"
    mod_freq = df["mod_freq"].iloc[0] if "mod_freq" in df.columns else config.MOD_FREQ
    masker_itd = df["masker_itd_us"].iloc[0] if "masker_itd_us" in df.columns else config.MASKER_ITD_US
    
    subtitle = f"Test: {test_freq}Hz, Mod: {mod_type} ({mod_freq}Hz), Masker ITD: {masker_itd}µs"

    fig, ax = plt.subplots(figsize=(max(6, n_itd * 1.5), 5))

    # 折れ線グラフとしてプロット
    ax.plot(
        itd_list, threshold_vals,
        marker="o", color="#2A9D8F", linewidth=2.0, markersize=8,
        label="Pulsation Threshold"
    )

    # 値ラベル
    for x, y in zip(itd_list, threshold_vals):
        if not np.isnan(y):
            ax.text(
                x, y + 1.5,  # 点の少し上に表示
                f"{y:.1f}", ha="center", va="bottom", fontsize=9, color="#2A9D8F",
                fontweight="bold",
            )

    ax.set_xticks(itd_list)
    ax.set_xticklabels([f"{itd} µs" for itd in itd_list])
    ax.set_xlabel("ITD condition")
    ax.set_ylabel("Pulsation threshold (dB SL in 1kHz)")
    ax.set_title(f"Pulsation threshold (Subject: {subject})\n{subtitle}",
                  fontsize=12, fontweight="bold")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)
    
    # Y軸の範囲を少し広めにとる
    min_y = np.nanmin(threshold_vals) - 10
    max_y = np.nanmax(threshold_vals) + 10
    ax.set_ylim(min_y, max_y)

    plt.tight_layout()
    summary_path = save_prefix + "_summary.png"
    fig.savefig(summary_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {summary_path}")

    # 表示
    plt.show()


# ────────────────────────────────────────────
# メイン
# ────────────────────────────────────────────

def main() -> None:
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    df, path = load_csv(csv_path)

    # 結果サマリーをコンソール出力
    print("\n=== 閾値サマリー ===")
    print(f"{'ITD(us)':>10}  {'Threshold(dB)':>15}")
    for _, row in df.sort_values("itd_us").iterrows():
        print(
            f"{int(row['itd_us']):>10}  "
            f"{row['threshold_db']:>15.2f}"
        )

    # 保存パスのプレフィックス: CSV と同じフォルダ・同じ幹
    stem = os.path.splitext(path)[0]
    plot_all(df, stem)
    print("\n完了しました。")


if __name__ == "__main__":
    main()
