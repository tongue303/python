# Binaural Pulsation Threshold Measurement

両耳間時間差 (ITD) をパラメータとした **パルセーション閾値** を、Jesteadt (1980) の2系列適応的測定法で計測する PsychoPy 実験プログラムです。

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
| **マスカー (M)** | ピンクノイズ（165 ms × 4 区間）|
| **テスト信号 (T)** | 500 Hz 正弦波（165 ms × 3 区間）|
| **刺激パターン** | M-T-M-T-M-T-M（クロスフェード 20 ms、全長 約 1035 ms）|
| **独立変数** | テスト信号の微細構造 ITD（µs 単位でダイアログから入力）|
| **従属変数** | パルセーション閾値（テスト信号レベル dB FS）|
| **マスカーレベル** | Phase 1 で測定した 1 kHz 聴取閾値 +60 dB SL |
| **課題** | 「断続 (Discontinuous)」または「連続 (Continuous)」の 2 択判断 |

---

## ディレクトリ構成

```
BinauralPulsationThreshold/
├── main.py               # エントリーポイント
├── config.py             # 全スクリプト共通の設定値
├── phase1_threshold.py   # Phase 1: 1 kHz 聴取閾値測定
├── phase2_stimulus.py    # Phase 2: 交番刺激音の生成
├── phase2_adaptive.py    # Phase 2: Jesteadt 2 系列適応アルゴリズム
├── data_recorder.py      # 試行データの蓄積・CSV 書き出し
├── plot_results.py       # 結果の読み込み・可視化
├── test_algorithm.py     # アルゴリズム動作確認用スクリプト
├── initPlan.md           # 設計計画書
└── data/                 # 実験データ保存先（自動生成）
    └── <SubjectID>_<timestamp>.csv
```

---

## 必要環境

| パッケージ | 用途 |
|---|---|
| [PsychoPy](https://www.psychopy.org/) ≥ 2024 | 刺激提示・応答収集 |
| NumPy | 波形配列の生成・演算 |
| pandas | CSV 読み込み・集計 |
| matplotlib | 結果グラフ描画 |

PsychoPy のスタンドアロン版を使用する場合は、同梱の Python 環境が上記ライブラリを含みます。

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
 ├─ Phase 2: ITD 条件をランダム順に実施
 │    ├─ Track A（高レベル → 下降）: 「断続 71%」の閾値を探索
 │    └─ Track B（低レベル → 上昇）: 「連続 71%」の閾値を探索
 │         ※ Track A / B はランダムにインターリーブ提示
 │
 ├─ CSV 保存（data/<SubjectID>_<timestamp>.csv）
 │
 └─ 結果グラフ自動生成 → PNG 保存
```

---

## 実行方法

### 通常実行（実験全体）

```bash
python main.py
```

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
| Phase 2 | `D` | Discontinuous（断続）|
| Phase 2 | `C` | Continuous（連続）|
| 共通 | `Escape` | 実験を中断・終了 |

---

## 設定パラメータ (config.py)

主要なパラメータを下表に示します。変更は `config.py` を直接編集してください。

### 音声基本設定

| 定数 | デフォルト値 | 説明 |
|---|---|---|
| `SAMPLE_RATE` | 44100 Hz | サンプリングレート |
| `RAMP_DURATION` | 0.020 s | コサインテーパー長 |

### Phase 1（1 kHz 聴取閾値）

| 定数 | デフォルト値 | 説明 |
|---|---|---|
| `PHASE1_FREQ` | 1000.0 Hz | 純音周波数 |
| `PHASE1_DURATION` | 0.500 s | 1 呈示あたりの長さ |
| `PHASE1_START_LEVEL` | −20.0 dB FS | 開始レベル |
| `PHASE1_STEP_LARGE` | 4.0 dB | 初期ステップ幅 |
| `PHASE1_STEP_SMALL` | 2.0 dB | 収束後ステップ幅 |
| `PHASE1_TOTAL_REVERSALS` | 8 回 | 終了に必要な反転回数 |

### Phase 2（適応的測定）

| 定数 | デフォルト値 | 説明 |
|---|---|---|
| `TEST_FREQ` | 500.0 Hz | テスト信号周波数 |
| `MASKER_DURATION` | 0.165 s | M 区間長 |
| `TEST_DURATION` | 0.165 s | T 区間長 |
| `CROSSFADE_DURATION` | 0.020 s | クロスフェード長 |
| `SL_OFFSET_DB` | 60.0 dB | マスカーレベルのオフセット |
| `TRACK_A_START_LEVEL` | −10.0 dB | Track A 開始オフセット（マスカー比）|
| `TRACK_B_START_LEVEL` | −50.0 dB | Track B 開始オフセット（マスカー比）|
| `STEP_LARGE` | 2.0 dB | 初期ステップ幅 |
| `STEP_SMALL` | 1.0 dB | 収束後ステップ幅 |
| `TOTAL_REVERSALS` | 8 回 | Track 終了に必要な反転回数 |

---

## データ出力

実験終了後、`data/` フォルダに CSV が保存されます。

**ファイル名**: `data/<SubjectID>_<YYYYMMDD_HHMMSS>.csv`

### CSV 列仕様

| 列名 | 型 | 内容 |
|---|---|---|
| `subject_id` | str | 被験者 ID |
| `itd_us` | int | ITD 条件（µs）|
| `track` | str | `A` または `B` |
| `trial_no` | int | 全体試行番号 |
| `level_db` | float | 提示テスト信号レベル（dB FS）|
| `response` | str | `pulsating` / `continuous` |
| `is_reversal` | int | 反転ポイントなら `1`、それ以外 `0` |

### 閾値の算出方法

```
Track A 閾値 = 最終ステップ幅での反転レベルの平均
Track B 閾値 = 最終ステップ幅での反転レベルの平均
最終パルセーション閾値 = (Track A 閾値 + Track B 閾値) / 2
```

---

## 結果の可視化

実験終了時に `plot_results.py` が自動で呼ばれ、以下の 2 種類のグラフが PNG 保存されます。

| ファイル名 | 内容 |
|---|---|
| `data/<stem>_history.png` | 各 ITD 条件の試行履歴（Track A/B ライン、反転点マーカー、閾値水平線）|
| `data/<stem>_summary.png` | 全 ITD 条件の最終閾値まとめ棒グラフ |

### 単独実行

```bash
python plot_results.py                    # data/ 内の最新 CSV を自動選択
python plot_results.py data/P01_xxx.csv   # ファイルを指定
```

---

## 単体テスト用モード

各モジュールは単独実行でも動作確認が可能です。

```bash
# Phase 1 動作確認（PsychoPy ウィンドウで閾値測定を単独実行）
python phase1_threshold.py

# Phase 2 アルゴリズム確認（ランダム応答でシミュレーション、GUI 不要）
python phase2_adaptive.py
```

---

## 参考文献

- Jesteadt, W. (1980). An adaptive procedure for subjective judgments. *Perception & Psychophysics*, 28(1), 85–88.
