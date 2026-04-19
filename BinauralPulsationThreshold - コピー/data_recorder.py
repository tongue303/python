"""
data_recorder.py
================
データ記録・閾値算出モジュール

試行ごとのデータをメモリに蓄積し、最終的に CSV として書き出す。
"""

import csv
import os
from datetime import datetime

import config


class DataRecorder:
    """
    実験データを蓄積・保存するクラス。
    """

    # CSV の列定義
    FIELDNAMES = [
        "subject_id",
        "itd_us",
        "track",
        "trial_no",
        "level_db",
        "response",
        "is_reversal",
    ]

    def __init__(self) -> None:
        self._rows: list[dict] = []

    def add_trial(
        self,
        subject_id: str,
        itd_us: int,
        track: str,
        trial_no: int,
        level_db: float,
        response: str,
        is_reversal: bool,
    ) -> None:
        """
        1試行分のデータを追加する。

        Parameters
        ----------
        subject_id : str
        itd_us : int
            ITD (µs)。ラベル用の整数値。
        track : str
            "A" または "B"。
        trial_no : int
            通し試行番号（全体）。
        level_db : float
            提示テスト信号レベル (dB FS)。
        response : str
            "pulsating" または "continuous"。
        is_reversal : bool
            反転ポイントなら True。
        """
        self._rows.append({
            "subject_id": subject_id,
            "itd_us": itd_us,
            "track": track,
            "trial_no": trial_no,
            "level_db": f"{level_db:.4f}",
            "response": response,
            "is_reversal": int(is_reversal),
        })

    def save(self, subject_id: str) -> str:
        """
        蓄積データを CSV ファイルに書き出す。

        Parameters
        ----------
        subject_id : str

        Returns
        -------
        str
            保存した CSV のパス。
        """
        # data/ ディレクトリを作成（なければ）
        os.makedirs(config.DATA_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(config.DATA_DIR, f"{subject_id}_{timestamp}.csv")

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            writer.writerows(self._rows)

        return filename


def calculate_final_threshold(threshold_a: float, threshold_b: float) -> float:
    """
    Track A・B それぞれの推定閾値から最終パルセーション閾値を算出する。

    算出式: (threshold_A + threshold_B) / 2

    Parameters
    ----------
    threshold_a : float
        Track A の推定閾値 (dB FS)。
    threshold_b : float
        Track B の推定閾値 (dB FS)。

    Returns
    -------
    float
        最終パルセーション閾値 (dB FS)。
    """
    return (threshold_a + threshold_b) / 2.0
