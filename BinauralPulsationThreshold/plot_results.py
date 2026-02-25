"""
plot_results.py
===============
パルセーション閾値測定結果のポストプロセス・可視化スクリプト

機能:
  1. data/ フォルダ内の最新 CSV（または引数指定）を読み込む
  2. 各 ITD 条件 × Track A/B の試行履歴を折れ線グラフで表示
  3. 反転ポイントをマーカーで強調表示
  4. 各条件の最終閾値（Track A・B の反転平均の算術平均）をまとめた棒グラフを作成
  5. 図を PNG として保存

使い方:
  python plot_results.py                          # data/ 内の最新CSVを自動選択
  python plot_results.py data/P01_xxx.csv         # ファイルを指定
"""

import sys
import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ── 日本語フォント（環境に合わせて変更してください）──
plt.rcParams["font.family"] = "Meiryo"   # Windows: Meiryo / Mac: Hiragino Sans
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
    print(f"読み込み: {path}  ({len(df)} 行)")
    return df, path


# ────────────────────────────────────────────
# 閾値算出
# ────────────────────────────────────────────

def calc_thresholds(df: pd.DataFrame) -> pd.DataFrame:
    """
    ITD条件 × Track ごとの反転点平均と最終閾値を算出する。
    """
    rows = []
    for (itd, track), grp in df.groupby(["itd_us", "track"]):
        rev = grp[grp["is_reversal"] == 1]["level_db"]
        thr = rev.mean() if len(rev) > 0 else np.nan
        rows.append({"itd_us": itd, "track": track,
                     "n_reversals": len(rev), "threshold_db": thr})
    thr_df = pd.DataFrame(rows)

    # 最終閾値 = Track A と Track B の算術平均
    final_rows = []
    for itd, grp in thr_df.groupby("itd_us"):
        tA = grp.loc[grp["track"] == "A", "threshold_db"].values
        tB = grp.loc[grp["track"] == "B", "threshold_db"].values
        tA = tA[0] if len(tA) else np.nan
        tB = tB[0] if len(tB) else np.nan
        final = (tA + tB) / 2
        final_rows.append({"itd_us": itd, "thr_A": tA, "thr_B": tB,
                            "final_threshold_db": final})
    return thr_df, pd.DataFrame(final_rows)


# ────────────────────────────────────────────
# プロット
# ────────────────────────────────────────────

TRACK_COLOR = {"A": "#E76F51", "B": "#457B9D"}  # Track A=オレンジ, B=青

def plot_all(df: pd.DataFrame, thr_df: pd.DataFrame,
             final_df: pd.DataFrame, save_prefix: str) -> None:
    """
    1. 各 ITD 条件の試行履歴グラフ（Track A/B）
    2. 最終閾値まとめ棒グラフ
    を描画・保存する。
    """
    itd_list = sorted(df["itd_us"].unique())
    n_itd = len(itd_list)

    # ────────────────────────────────────────
    # ① 試行履歴グラフ（ITD条件ごとにサブプロット）
    # ────────────────────────────────────────
    fig, axes = plt.subplots(
        n_itd, 1,
        figsize=(12, 4.5 * n_itd),
        squeeze=False,
    )
    fig.suptitle("Track A / B trial history", fontsize=14, fontweight="bold", y=1.01)

    for row_idx, itd in enumerate(itd_list):
        ax = axes[row_idx][0]
        sub = df[df["itd_us"] == itd]

        for track in ["A", "B"]:
            t_sub = sub[sub["track"] == track].copy()
            if t_sub.empty:
                continue

            color = TRACK_COLOR[track]
            label_base = f"Track {track}"

            # 試行ラインと通常点
            ax.plot(
                t_sub["trial_no"], t_sub["level_db"],
                color=color, linewidth=1.2, alpha=0.7,
                label=label_base,
            )

            # 非反転点
            non_rev = t_sub[t_sub["is_reversal"] == 0]
            ax.scatter(
                non_rev["trial_no"], non_rev["level_db"],
                color=color, s=20, zorder=3, alpha=0.6,
            )

            # 反転点（大きいマーカー）
            rev = t_sub[t_sub["is_reversal"] == 1]
            ax.scatter(
                rev["trial_no"], rev["level_db"],
                color=color, s=100, marker="D", edgecolors="black",
                linewidths=0.8, zorder=4,
                label=f"Track {track} reversal",
            )

            # 反転平均を水平線で表示
            thr_row = thr_df[(thr_df["itd_us"] == itd) & (thr_df["track"] == track)]
            if not thr_row.empty:
                thr_val = thr_row["threshold_db"].values[0]
                if not np.isnan(thr_val):
                    ax.axhline(
                        thr_val, color=color, linewidth=1.5,
                        linestyle="--", alpha=0.8,
                        label=f"Track {track} average ({thr_val:.1f} dB)",
                    )

        # 最終閾値の帯
        final_row = final_df[final_df["itd_us"] == itd]
        if not final_row.empty:
            ft = final_row["final_threshold_db"].values[0]
            if not np.isnan(ft):
                ax.axhline(
                    ft, color="green", linewidth=2.0,
                    linestyle="-.", alpha=0.9,
                    label=f"Final threshold ({ft:.1f} dB)",
                )

        ax.set_title(f"ITD = {itd} µs", fontsize=11, fontweight="bold")
        ax.set_xlabel("Trial number")
        ax.set_ylabel("Test signal level (dB FS)")
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(1))
        ax.grid(True, which="major", linestyle="--", alpha=0.4)
        ax.grid(True, which="minor", linestyle=":", alpha=0.2)
        ax.legend(fontsize=8, loc="upper right")

    plt.tight_layout()
    history_path = save_prefix + "_history.png"
    fig.savefig(history_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {history_path}")
    # show() は全図保存後にまとめて呼ぶ

    # ────────────────────────────────────────
    # ② 最終閾値まとめ棒グラフ（ITD条件が複数の場合に有効）
    # ────────────────────────────────────────
    subject = df["subject_id"].iloc[0]
    fig2, ax2 = plt.subplots(figsize=(max(6, n_itd * 1.8), 5))

    x = np.arange(n_itd)
    width = 0.25

    thr_a_vals = [
        final_df.loc[final_df["itd_us"] == itd, "thr_A"].values[0]
        if itd in final_df["itd_us"].values else np.nan
        for itd in itd_list
    ]
    thr_b_vals = [
        final_df.loc[final_df["itd_us"] == itd, "thr_B"].values[0]
        if itd in final_df["itd_us"].values else np.nan
        for itd in itd_list
    ]
    final_vals = [
        final_df.loc[final_df["itd_us"] == itd, "final_threshold_db"].values[0]
        if itd in final_df["itd_us"].values else np.nan
        for itd in itd_list
    ]

    bars_a = ax2.bar(x - width, thr_a_vals, width, label="Track A average",
                     color=TRACK_COLOR["A"], alpha=0.8, edgecolor="black", linewidth=0.5)
    bars_b = ax2.bar(x,         thr_b_vals, width, label="Track B average",
                     color=TRACK_COLOR["B"], alpha=0.8, edgecolor="black", linewidth=0.5)
    bars_f = ax2.bar(x + width, final_vals, width, label="Final threshold (A+B)/2",
                     color="#2A9D8F", alpha=0.9, edgecolor="black", linewidth=0.5)

    # 値ラベル
    for bars in [bars_a, bars_b, bars_f]:
        for bar in bars:
            h = bar.get_height()
            if not np.isnan(h):
                ax2.text(
                    bar.get_x() + bar.get_width() / 2, h - 1.5,
                    f"{h:.1f}", ha="center", va="top", fontsize=8, color="white",
                    fontweight="bold",
                )

    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{itd} µs" for itd in itd_list])
    ax2.set_xlabel("ITD condition")
    ax2.set_ylabel("Pulsation threshold (dB FS)")
    ax2.set_title(f"Pulsation threshold summary  (Subject: {subject})",
                  fontsize=12, fontweight="bold")
    ax2.legend()
    ax2.grid(True, axis="y", linestyle="--", alpha=0.4)
    ax2.invert_yaxis()   # dB は低いほうが聞こえにくい → 下が低い方が直感的

    plt.tight_layout()
    summary_path = save_prefix + "_summary.png"
    fig2.savefig(summary_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {summary_path}")

    # 両グラフをまとめて表示（どちらかを閉じると両方終了）
    plt.show()


# ────────────────────────────────────────────
# メイン
# ────────────────────────────────────────────

def main() -> None:
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    df, path = load_csv(csv_path)

    thr_df, final_df = calc_thresholds(df)

    # 結果サマリーをコンソール出力
    print("\n=== 閾値サマリー ===")
    print(f"{'ITD(us)':>10}  {'Track A':>10}  {'Track B':>10}  {'Final Thr':>10}")
    for _, row in final_df.sort_values("itd_us").iterrows():
        print(
            f"{int(row['itd_us']):>10}  "
            f"{row['thr_A']:>10.2f}  "
            f"{row['thr_B']:>10.2f}  "
            f"{row['final_threshold_db']:>10.2f}"
        )

    # 保存パスのプレフィックス: CSV と同じフォルダ・同じ幹
    stem = os.path.splitext(path)[0]
    plot_all(df, thr_df, final_df, stem)
    print("\n完了しました。")


if __name__ == "__main__":
    main()
