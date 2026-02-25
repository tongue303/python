"""
main.py
=======
パルセーション閾値測定プログラム エントリーポイント

実行フロー:
  1. 初期ダイアログ: 被験者ID, ITDリスト入力
  2. Phase 1: 1kHz聴取閾値測定 → マスカーレベル算出
  3. Phase 2: 各ITD条件をランダム順で提示 → Track A/B インターリーブ
  4. CSV保存 → 終了
"""

import os
import random

from psychopy import visual, core, gui, event

import config
from phase1_threshold import run_phase1
from phase2_adaptive import run_itd_condition
from data_recorder import DataRecorder, calculate_final_threshold
from plot_results import load_csv, calc_thresholds, plot_all


# ────────────────────────────────────────────
# 初期ダイアログ
# ────────────────────────────────────────────

def show_dialog() -> tuple[str, list[int], float | None]:
    """
    被験者IDと測定するITDリスト、および既知のSL基準値を取得するダイアログ。

    Returns
    -------
    (subject_id, itd_list_us, sl_reference_db)
        sl_reference_db: 入力があればその値を使いPhase1をスキップ。
                         空欄なら None を返し、Phase1を実施する。
    """
    dlg = gui.Dlg(title="Pulsation Threshold Measurement")
    dlg.addField("Subject ID:", "P01")
    dlg.addField("ITD list (us, comma-separated):", "0, 200, 400")
    dlg.addField("SL reference (dB FS, blank = run Phase 1):", "")

    ok = dlg.show()
    if not ok:
        core.quit()

    subject_id   = str(dlg.data[0]).strip()
    raw_itds     = str(dlg.data[1]).strip()
    raw_sl       = str(dlg.data[2]).strip()

    # ITDリストのパース
    itd_list_us = []
    for token in raw_itds.split(","):
        token = token.strip()
        if token.lstrip("-").isdigit():
            itd_list_us.append(int(token))

    if not itd_list_us:
        raise ValueError(f"Please enter a valid ITD list: '{raw_itds}'")

    # SL基準値のパース（空欄なら None）
    sl_reference_db: float | None = None
    if raw_sl != "":
        try:
            sl_reference_db = float(raw_sl)
        except ValueError:
            raise ValueError(f"SL reference must be a number: '{raw_sl}'")

    return subject_id, itd_list_us, sl_reference_db


# ────────────────────────────────────────────
# メイン
# ────────────────────────────────────────────

def main() -> None:
    # ── 初期ダイアログ ──
    subject_id, itd_list_us, sl_reference_db = show_dialog()

    # µs → 秒 変換
    itd_list_sec = [us * 1e-6 for us in itd_list_us]

    # ── ウィンドウ生成 ──
    win = visual.Window(
        size=(1600, 900),
        fullscr=False,
        color="black",
        units="norm",
        screen=0,
    )
    win.setMouseVisible(False)

    recorder = DataRecorder()

    # ── Phase 1: 1kHz聴取閾値測定（sl_reference_db が未入力の場合のみ）──
    if sl_reference_db is None:
        print("Running Phase 1: 1kHz threshold measurement...")
        sl_reference_db = run_phase1(win)
    else:
        print(f"Phase 1 skipped. Using SL reference = {sl_reference_db:.2f} dB FS")
    masker_level_db = sl_reference_db + config.SL_OFFSET_DB

    # ── Phase 2: ITD条件をランダム順に実施 ──
    itd_order = list(range(len(itd_list_us)))
    random.shuffle(itd_order)

    final_thresholds: list[dict] = []

    for idx in itd_order:
        itd_us = itd_list_us[idx]
        itd_sec = itd_list_sec[idx]

        thr_a, thr_b = run_itd_condition(
            win=win,
            masker_level_db=masker_level_db,
            itd_seconds=itd_sec,
            subject_id=subject_id,
            itd_label_us=itd_us,
            recorder=recorder,
        )

        final_thr = calculate_final_threshold(thr_a, thr_b)
        final_thresholds.append({
            "itd_us": itd_us,
            "threshold_A_dBFS": thr_a,
            "threshold_B_dBFS": thr_b,
            "final_threshold_dBFS": final_thr,
        })

    # ── データ保存 ──
    csv_path = recorder.save(subject_id)

    print(f"\n=== Experiment finished: {subject_id} ===")
    print(f"Phase 1 SL ref: {sl_reference_db:.2f} dB FS")
    print(f"Masker level:   {masker_level_db:.2f} dB FS\n")
    print(f"{'ITD(us)':>10} {'Track A':>10} {'Track B':>10} {'Final Thr':>10}")
    for row in sorted(final_thresholds, key=lambda r: r["itd_us"]):
        print(
            f"{row['itd_us']:>10} "
            f"{row['threshold_A_dBFS']:>10.2f} "
            f"{row['threshold_B_dBFS']:>10.2f} "
            f"{row['final_threshold_dBFS']:>10.2f}"
        )
    print(f"\nCSV saved: {csv_path}")

    # ── 終了画面 ──
    msg = visual.TextStim(
        win,
        text=(
            "Experiment finished\n\n"
            f"Results saved to {csv_path}\n\n"
            "[Space] to show graphs & exit"
        ),
        height=0.06, wrapWidth=1.8, color="white",
    )
    msg.draw()
    win.flip()
    event.waitKeys(keyList=["space"])

    win.close()  # PsychoPy ウィンドウを先に閉じる

    # ── 結果グラフを自動生成 ──
    print("Generating result plots...")
    df_result, _ = load_csv(csv_path)
    thr_df, final_df = calc_thresholds(df_result)
    stem = os.path.splitext(csv_path)[0]
    plot_all(df_result, thr_df, final_df, stem)

    core.quit()


if __name__ == "__main__":
    main()
