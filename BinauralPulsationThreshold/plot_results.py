# -*- coding: utf-8 -*-
"""
plot_results.py
===============
パルセーション閾値測定結果のポストプロセス・可視化スクリプト（1-up 1-down 適応法対応）

機能:
  1. data/ フォルダ内の最新 CSV（または引数指定）を読み込む
  2. ITD条件ごとに階段法の推移グラフ（Staircase plot）を描画・保存
  3. ITDごとの最終的なパルセーション閾値を折れ線グラフで描画・保存
"""

import sys
import os
import glob
import platform
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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
    if path is None:
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        files = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
        if not files:
            raise FileNotFoundError("data/ フォルダに CSV ファイルが見つかりません。")
        path = files[-1]

    df = pd.read_csv(path)

    # threshold_db が空文字("")の場合は NaN にする
    if "threshold_db" in df.columns:
        df["threshold_db"] = pd.to_numeric(df["threshold_db"], errors="coerce")
    
    if "sl_reference_db" in df.columns and "threshold_db" in df.columns:
        df["threshold_db"] = df["threshold_db"] - df["sl_reference_db"]

    print(f"読み込み: {path}  ({len(df)} 行)")
    return df, path


# ────────────────────────────────────────────
# プロット
# ────────────────────────────────────────────

def plot_staircase(df_itd: pd.DataFrame, itd_us: float, save_prefix: str, subtitle: str) -> None:
    """
    1つのITD条件に対する階段法の履歴をプロットする。
    """
    trials = df_itd["trial_no"].values
    levels = df_itd["level_db"].values
    responses = df_itd["response"].values
    is_reversal = df_itd["is_reversal"].values

    fig, ax = plt.subplots(figsize=(8, 5))
    
    # 全体の線
    ax.plot(trials, levels, color="gray", linestyle="-", marker="None", zorder=1)

    # 応答ごとのマーカー
    # Continuous (連続) -> 青い丸
    mask_c = (responses == "continuous")
    ax.scatter(trials[mask_c], levels[mask_c], c="blue", marker="o", s=40, label="Continuous", zorder=2)
    
    # Interrupted (途切れ) -> 赤いバツ
    mask_i = (responses == "interrupted")
    ax.scatter(trials[mask_i], levels[mask_i], c="red", marker="x", s=40, label="Interrupted", zorder=2)

    # 反転ポイントの強調
    mask_rev = (is_reversal == True)
    if mask_rev.any():
        ax.scatter(trials[mask_rev], levels[mask_rev], facecolors="none", edgecolors="black", s=100, linewidths=1.5, label="Reversal", zorder=3)

    # 閾値の水平線
    final_thresh = df_itd["threshold_db"].dropna().unique()
    if len(final_thresh) > 0:
        thresh_val = final_thresh[0]
        # ただしここでは FS基準でプロットしているので、threshold_db(SL基準に変換済み)をFS基準に戻す
        sl_ref = df_itd["sl_reference_db"].iloc[0]
        thresh_fs = thresh_val + sl_ref
        ax.axhline(thresh_fs, color="green", linestyle="--", label=f"Threshold: {thresh_fs:.1f} dB")

    ax.set_title(f"Staircase tracking (ITD = {int(itd_us)} µs)\n{subtitle}", fontsize=11)
    ax.set_xlabel("Trial number")
    ax.set_ylabel("Target level (dB FS)")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()

    plt.tight_layout()
    out_path = f"{save_prefix}_staircase_{int(itd_us)}us.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close(fig)

def plot_all(df: pd.DataFrame, save_prefix: str) -> None:
    """
    ITDごとの閾値を折れ線グラフとして描画・保存する。
    """
    # ITDごとに一意な閾値を抽出
    summary_data = []
    for itd, grp in df.groupby("itd_us"):
        thresh_vals = grp["threshold_db"].dropna().unique()
        if len(thresh_vals) > 0:
            summary_data.append({"itd_us": itd, "threshold_db": thresh_vals[0]})
    
    if not summary_data:
        print("有効な閾値データが見つかりません。")
        return

    df_summary = pd.DataFrame(summary_data).sort_values("itd_us")
    
    itd_list = df_summary["itd_us"].values
    threshold_vals = df_summary["threshold_db"].values
    n_itd = len(itd_list)
    subject = df["subject_id"].iloc[0]
    
    test_freq = df["test_freq"].iloc[0] if "test_freq" in df.columns else config.TEST_FREQ
    mod_type = df["mod_type"].iloc[0] if "mod_type" in df.columns else "None"
    mod_freq = df["mod_freq"].iloc[0] if "mod_freq" in df.columns else config.MOD_FREQ
    masker_itd = df["masker_itd_us"].iloc[0] if "masker_itd_us" in df.columns else config.MASKER_ITD_US
    
    subtitle = f"Test: {test_freq}Hz, Mod: {mod_type} ({mod_freq}Hz), Masker ITD: {masker_itd}µs"

    fig, ax = plt.subplots(figsize=(max(6, n_itd * 1.5), 5))

    ax.plot(
        itd_list, threshold_vals,
        marker="o", color="#2A9D8F", linewidth=2.0, markersize=8,
        label="Pulsation Threshold"
    )

    for x, y in zip(itd_list, threshold_vals):
        if not np.isnan(y):
            ax.text(
                x, y + 1.5,
                f"{y:.1f}", ha="center", va="bottom", fontsize=9, color="#2A9D8F",
                fontweight="bold",
            )

    ax.set_xticks(itd_list)
    ax.set_xticklabels([f"{int(itd)} µs" for itd in itd_list])
    ax.set_xlabel("ITD condition")
    ax.set_ylabel("Pulsation threshold (dB SL in 1kHz)")
    ax.set_title(f"Pulsation threshold (Subject: {subject})\n{subtitle}",
                  fontsize=12, fontweight="bold")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)
    
    min_y = np.nanmin(threshold_vals) - 10
    max_y = np.nanmax(threshold_vals) + 10
    ax.set_ylim(min_y, max_y)

    plt.tight_layout()
    summary_path = save_prefix + "_summary.png"
    fig.savefig(summary_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {summary_path}")
    plt.show()


# ────────────────────────────────────────────
# メイン
# ────────────────────────────────────────────

def main() -> None:
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    df, path = load_csv(csv_path)

    stem = os.path.splitext(path)[0]
    
    test_freq = df["test_freq"].iloc[0] if "test_freq" in df.columns else config.TEST_FREQ
    mod_type = df["mod_type"].iloc[0] if "mod_type" in df.columns else "None"
    mod_freq = df["mod_freq"].iloc[0] if "mod_freq" in df.columns else config.MOD_FREQ
    masker_itd = df["masker_itd_us"].iloc[0] if "masker_itd_us" in df.columns else config.MASKER_ITD_US
    subtitle = f"Test: {test_freq}Hz, Mod: {mod_type} ({mod_freq}Hz), Masker ITD: {masker_itd}µs"

    # ITDごとにStaircaseをプロット
    for itd, grp in df.groupby("itd_us"):
        plot_staircase(grp, itd, stem, subtitle)

    # 全体のサマリーをプロット
    print("\n=== 閾値サマリー ===")
    print(f"{'ITD(us)':>10}  {'Threshold(dB SL)':>16}")
    summary_data = []
    for itd, grp in df.groupby("itd_us"):
        thresh_vals = grp["threshold_db"].dropna().unique()
        if len(thresh_vals) > 0:
            print(f"{int(itd):>10}  {thresh_vals[0]:>16.2f}")
    
    plot_all(df, stem)
    print("\n完了しました。")


if __name__ == "__main__":
    main()
