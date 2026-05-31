# Binaural Pulsation Threshold Measurement

両耳間時間差 (ITD) をパラメータとした **パルセーション閾値** を、**調整法 (Method of Adjustment)** で計測する PsychoPy 実験プログラムです。

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
10. [トラブルシューティング・技術的最適化](#トラブルシューティング技術的最適化)

---

## 実験の概要

| 項目 | 内容 |
|---|---|
| **マスカー (M)** | バンドパスノイズ（中心周波数 = テスト周波数、通過帯域 fc/2 〜 fc×2、±1 オクターブ対称、145 ms × 3 区間）|
| **テスト信号 (T)** | 500 Hz 正弦波（145 ms × 4 区間）|
| **刺激パターン** | T-M-T-M-T-M-T-S（クロスフェード 20 ms、全長 約 1035 ms）|
| **独立変数** | テスト信号の微細構造 ITD（µs 単位でダイアログから入力）|
| **従属変数** | パルセーション閾値（テスト信号レベル dB FS）|
| **マスカーレベル** | Phase 1 で測定した 1 kHz 聴取閾値 + 目的 SL (デフォルト: 40 dB SL) |
| **課題** | 被験者が自らテスト信号の音量を上下させ、「断続的」から「連続的」に聴こえ始める境界を決定 |

---

## ディレクトリ構成

```
BinauralPulsationThreshold/
├── main.py               # エントリーポイント
├── config.py             # 全スクリプト共通の設定値
├── phase1_threshold.py   # Phase 1: 1 kHz 聴取閾値測定
├── phase2_stimulus.py    # Phase 2: 交番刺激音の生成
├── phase2_adjustment.py  # Phase 2: 調整法 (Method of Adjustment) による閾値測定
├── data_recorder.py      # 試行データの蓄積・CSV 書き出し
├── plot_results.py       # 結果の読み込み・可視化
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
| SciPy | バンドパスフィルタ（マスカー生成）|
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
 │    └─ 測定閾値 → マスカーレベル = 閾値 + 40 dB SL (TARGET_SL)
 │
 ├─ Phase 2: ITD 条件をランダム順に実施
 │    └─ 調整法（Method of Adjustment）:
 │         被験者が自らテスト信号の音量を上下させ、ノイズの間で
 │         テスト音が途切れることなく「連続」して聞こえ始める境界を探索・決定
 │
 ├─ CSV 保存（data/<SubjectID>_<timestamp>.csv）
 │
 └─ 結果グラフ自動生成 → PNG 保存
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
| Phase 2 | `↑` (Up) | テスト音量を上げる |
| Phase 2 | `↓` (Down) | テスト音量を下げる |
| Phase 2 | `Enter` | 閾値を決定（登録）し、次の条件へ進む |
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
| `PHASE1_STEP_LARGE` | 2.0 dB | 初期ステップ幅 |
| `PHASE1_STEP_SMALL` | 1.0 dB | 収束後ステップ幅 |

### Phase 2（調整法）

| 定数 | デフォルト値 | 説明 |
|---|---|---|
| `TEST_FREQ` | 500.0 Hz | テスト信号周波数 |
| `MASKER_DURATION` | 0.145 s | M 区間長 |
| `TEST_DURATION` | 0.145 s | T 区間長 |
| `CROSSFADE_DURATION` | 0.020 s | クロスフェード長 |
| `TARGET_SL` | 40.0 dB | マスカーの目標SL |
| `ADJUSTMENT_START_LEVEL` | +10.0 dB | 開始レベル（マスカーレベルからのオフセット）|
| `ADJUSTMENT_STEP` | 1.0 dB | 1回のキー入力での音量変化ステップ |

---

## データ出力

実験終了後、`data/` フォルダに CSV が保存されます。

**ファイル名**: `data/<SubjectID>_<YYYYMMDD_HHMMSS>.csv`

### CSV 列仕様

| 列名 | 型 | 内容 |
|---|---|---|
| `subject_id` | str | 被験者 ID |
| `sl_reference_db` | float | 1kHz聴取閾値（dB FS）|
| `test_freq` | float | テスト周波数（Hz）|
| `mod_freq` | float | 変調周波数（Hz）|
| `mod_type` | str | 変調タイプ |
| `masker_itd_us` | int | マスカー ITD（µs）|
| `itd_us` | int | テスト信号 ITD 条件（µs）|
| `threshold_db` | float | 被験者が決定した閾値（dB FS）|

---

## 結果の可視化

実験終了時に `plot_results.py` が自動で呼ばれ、以下のグラフが PNG 保存されます。

| ファイル名 | 内容 |
|---|---|
| `data/<stem>_summary.png` | ITD 条件ごとの最終閾値を示す折れ線グラフ |

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
```

---

## トラブルシューティング・技術的最適化

本プログラムは長時間の実験にも耐えられるよう、PsychoPyのオーディオバックエンド（PTB: Psychtoolbox）に関する以下の最適化を施しています。

- **リソースリークの防止**: 
  音量や波形を動的に変更する際、新しい `Sound` オブジェクトを毎ターン生成するとPTBのストリームが蓄積し、後半になるにつれ処理落ちや音の途切れ（プチプチ音）が発生する問題があります。本プログラムでは最初に1つだけダミーの `Sound` オブジェクトを生成し、以降は `snd.setSound(波形)` を用いてオブジェクトを使い回すことでリソースリークを完全に防止しています。
- **自然な再生リズムの維持**: 
  音量調整法（Phase 2: Adjustment）において、再生途中に音量変更キーが押されてもそのターン（T-M-T-M-T-M-T-S）の再生を強制終了させず、バックグラウンドで音量変更を予約し、次のターンの開始時に適用する仕様になっています。これにより、判断の要となる連続した刺激音のリズムが崩れることを防いでいます。
