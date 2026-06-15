# Binaural Pulsation Threshold Measurement

両耳間時間差 (ITD) をパラメータとした **パルセーション閾値** を、Experiment C に準拠した **1-up/1-down 階段法 (Staircase method)** で計測する PsychoPy 実験プログラムです。

---

## 目次

1. [実験の概要](#実験の概要)
2. [ディレクトリ構成](#ディレクトリ構成)
3. [必要環境](#必要環境)
4. [実験の流れ](#実験の流れ)
5. [実行方法](#実行方法)
6. [設定パラメータ (config.py)](#設定パラメータ-configpy)
7. [データ出力](#データ出力)
8. [結果の可視化](#結果の可視化)
9. [単体テスト用モード](#単体テスト用モード)
10. [参考文献](#参考文献)

---

## 実験の概要

| 項目 | 内容 |
|---|---|
| **マスカー (M)** | バンドパスノイズ（中心周波数 = テスト周波数、通過帯域 fc/2 〜 fc×2、±1 オクターブ対称、165 ms × 4 区間）|
| **テスト信号 (T)** | 500 Hz 正弦波（165 ms × 3 区間）|
| **刺激パターン** | M-T-M-T-M-T-M（クロスフェード 20 ms、全長 約 1035 ms）|
| **独立変数** | テスト信号の微細構造 ITD（µs 単位でダイアログから入力）|
| **従属変数** | パルセーション閾値（テスト信号レベル dB FS）|
| **マスカーレベル** | Phase 1 で測定した 1 kHz 聴取閾値 +60 dB SL |
| **課題** | 「連続 (Continuous)」または「途切れ (Interrupted)」の 2 択判断 |
| **測定アルゴリズム**| 1-up/1-down 階段法 (Staircase Method)|

---

## ディレクトリ構成

```
BinauralPulsationThreshold/
├── main.py               # エントリーポイント
├── config.py             # 全スクリプト共通の設定値
├── phase1_threshold.py   # Phase 1: 1 kHz 聴取閾値測定
├── phase2_stimulus.py    # Phase 2: 交番刺激音の生成
├── phase2_1up1down.py    # Phase 2: 1-up/1-down 階段法 (Experiment C 準拠)
├── data_recorder.py      # 試行データの蓄積・CSV 書き出し (Long Format対応)
├── plot_results.py       # 結果の読み込み・可視化 (Staircase Plot対応)
└── data/                 # 実験データ保存先（自動生成）
    └── <SubjectID>_<timestamp>.csv
```

---

## 必要環境

| パッケージ | 用途 |
|---|---|
| [PsychoPy](https://www.psychopy.org/) ≥ 2024 | 刺激提示・応答収集 |
| NumPy | 波形配列の生成・演算 |
| SciPy | バンドパスフィルタ（マスカー生成）|
| pandas | CSV 読み込み・集計 |
| matplotlib | 結果グラフ描画 |

---

## 実験の流れ

```
起動
 │
 ├─ [ダイアログ] 被験者ID / ITD リスト（µs） / SL 基準値（空欄でPhase 1実施）
 │
 ├─ Phase 1: 1 kHz 純音の聴取閾値測定（2-down 1-up 階段法）
 │    └─ 測定閾値 → マスカーレベル = 閾値 + 60 dB SL
 │
 ├─ Phase 2: ITD 条件をランダム順に実施 (1-up/1-down 階段法)
 │    ├─ 1試行ごとに M-T-M-T-M-T-M の刺激パターンを再生
 │    ├─ 回答: 「連続 (Continuous)」  → ターゲットレベル UP (+ステップ幅)
 │    └─ 回答: 「途切れ (Interrupted)」 → ターゲットレベル DOWN (-ステップ幅)
 │         ※ 反転回数に応じてステップ幅が縮小 (6.0 -> 3.0 -> 0.5 dB)
 │         ※ 反転が 10 回に達した時点で終了
 │
 ├─ CSV 保存（data/<SubjectID>_<timestamp>.csv）
 │
 └─ 結果グラフ自動生成 (階段法グラフ & サマリー) → PNG 保存
```

---

## 実行方法

### 通常実行（実験全体）

PsychoPy を起動し、Coder ビューから `main.py` を開いて実行 (Run) してください。

起動すると PsychoPy ダイアログが表示されます。

| フィールド | 入力例 | 説明 |
|---|---|---|
| Subject ID | `P01` | 被験者識別子 |
| ITD list (us) | `0, 200, 400` | 測定する ITD 条件（カンマ区切り）|
| SL reference (dB FS) | *(空欄)* | 空欄時は Phase 1 を自動実施 |

### キー操作

| フェーズ | キー | 意味 |
|---|---|---|
| Phase 1 | `Y` | 聴こえた |
| Phase 1 | `N` | 聴こえなかった |
| Phase 2 | `C` | Continuous（連続して聞こえた）|
| Phase 2 | `I` | Interrupted（途切れて聞こえた）|
| 共通 | `Escape` | 実験を中断・終了 |

---

## 設定パラメータ (config.py)

主要なパラメータを下表に示します。変更は `config.py` を直接編集してください。

### Phase 2（適応的測定: 1-up/1-down 階段法）

| 定数 | デフォルト値 | 説明 |
|---|---|---|
| `ADAPTIVE_INITIAL_STEP_SIZE`| 6.0 dB | 初期ステップ幅 |
| `ADAPTIVE_SECOND_STEP_SIZE` | 3.0 dB | 2回反転後のステップ幅 |
| `ADAPTIVE_FINAL_STEP_SIZE`  | 0.5 dB | 4回反転後のステップ幅 |
| `ADAPTIVE_MAX_REVERSALS`    | 10 回 | ブロック終了に必要な反転回数 |
| `ADAPTIVE_NUM_REVERSALS_FOR_MEAN` | 6 回 | 閾値計算に用いる反転ポイントの数 |
| `ADAPTIVE_INITIAL_TARGET_OFFSET` | 12.0 dB | マスカーレベルに対する初期ターゲットレベルの目安 |
| `ADAPTIVE_ROVING_RANGE`     | 3.0 dB | 初期レベルに加えるジッター（カンニング防止）幅 |

---

## データ出力

実験終了後、`data/` フォルダに CSV が保存されます。各試行ごとのデータが1行に記録されます（Long Format）。

**ファイル名**: `data/<SubjectID>_<YYYYMMDD_HHMMSS>.csv`

### CSV 列仕様

| 列名 | 型 | 内容 |
|---|---|---|
| `subject_id` | str | 被験者 ID |
| `sl_reference_db` | float | 1kHz閾値 |
| `itd_us` | int | ITD 条件（µs）|
| `track` | str | トラック名 (`1up1down`) |
| `trial_no` | int | 試行番号 |
| `level_db` | float | 提示テスト信号レベル（dB FS）|
| `response` | str | `continuous` / `interrupted` |
| `is_reversal`| bool | 反転ポイントなら `True`、それ以外 `False` |
| `threshold_db` | float | 算出された最終閾値（各ITDの全ての行に追記される） |
| `reversal_levels` | str | 記録された10個の反転レベル（JSON配列文字列）|

### 閾値の算出方法

最後の6回分（10回反転中、インデックス4〜9）の反転時ターゲットレベルの算術平均をパルセーション閾値とします。

---

## 結果の可視化

実験終了時に `plot_results.py` が自動で呼ばれ、以下の 2 種類のグラフが PNG 保存されます。

| ファイル名 | 内容 |
|---|---|
| `data/<stem>_staircase_<itd>us.png` | 各 ITD 条件の試行ごとの階段法の推移グラフ。Continuous / Interrupted の応答や反転ポイント、最終閾値のラインが可視化されます。 |
| `data/<stem>_summary.png` | 全 ITD 条件の最終閾値を比較する折れ線グラフ |

---

## 単体テスト用モード

各モジュールは単独実行でも動作確認が可能です。

```bash
# Phase 1 動作確認
python phase1_threshold.py

# Phase 2 1-up/1-down 階段法アルゴリズム確認（ランダム応答でシミュレーション）
python phase2_1up1down.py
```

---

## 参考文献

- Experiment C 仕様 (1-up/1-down staircase method)

