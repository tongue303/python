# -*- coding: utf-8 -*-
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
        "sl_reference_db",
        "test_freq",
        "mod_freq",
        "mod_type",
        "masker_itd_us",
        "itd_us",
        "threshold_db",
    ]

    def __init__(self) -> None:
        self._rows: list[dict] = []

    def add_result(
        self,
        subject_id: str,
        sl_reference_db: float,
        test_freq: float,
        mod_freq: float,
        mod_type: str,
        masker_itd_us: int,
        itd_us: int,
        threshold_db: float,
    ) -> None:
        """
        1つのITD条件の結果を追加する。
        """
        self._rows.append({
            "subject_id": subject_id,
            "sl_reference_db": sl_reference_db,
            "test_freq": test_freq,
            "mod_freq": mod_freq,
            "mod_type": mod_type,
            "masker_itd_us": masker_itd_us,
            "itd_us": itd_us,
            "threshold_db": f"{threshold_db:.4f}",
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

        with open(filename, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            writer.writerows(self._rows)

        return filename
