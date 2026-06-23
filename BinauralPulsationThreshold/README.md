# Binaural Pulsation Threshold Measurement

両耳間時間差 (ITD) をパラメータとした **パルセーション閾値** を、Experiment C に準拠した **1-up/1-down 階段法 (Staircase method)** で計測する実験プログラムです。

本リポジトリには、PsychoPyを利用した **Python デスクトップアプリ版** と、ブラウザだけで実行可能な **Web アプリケーション版** の2種類の実装が含まれています。

---

## 目次

1. [実験の概要](#実験の概要)
2. [ディレクトリ構成](#ディレクトリ構成)
3. [Web アプリケーション版の実行方法](#web-アプリケーション版の実行方法)
4. [Python デスクトップアプリ版の実行方法](#python-デスクトップアプリ版の実行方法)
5. [設定パラメータ (config.py / config.ts)](#設定パラメータ)
6. [データ出力と結果の可視化](#データ出力と結果の可視化)
7. [参考文献](#参考文献)

---

## 実験の概要

| 項目 | 内容 |
|---|---|
| **マスカー (M)** | バンドパスノイズ（中心周波数 = テスト周波数、通過帯域 fc/2 〜 fc×2、±1 オクターブ対称、165 ms × 4 区間）|
| **テスト信号 (T)** | 500 Hz 正弦波（165 ms × 3 区間）|
| **刺激パターン** | M-T-M-T-M-T-M（クロスフェード 20 ms、全長 約 1035 ms）|
| **独立変数** | テスト信号の微細構造 ITD（µs 単位で入力）|
| **従属変数** | パルセーション閾値（テスト信号レベル dB FS）|
| **マスカーレベル** | Phase 1 で測定した 1 kHz 聴取閾値 +60 dB SL |
| **課題** | 「連続 (Continuous)」または「途切れ (Interrupted)」の 2 択判断 |
| **測定アルゴリズム**| Phase 1: 2-down 1-up (初期は加速ルール) / Phase 2: 1-up 1-down 階段法 |

---

## ディレクトリ構成

```text
BinauralPulsationThreshold/
├── pyproject.toml        # Python版の依存関係定義 (uv対応)
├── uv.lock               # Python版のロックファイル
├── main.py               # Python版のエントリーポイント
├── config.py             # Python版の設定ファイル
├── phase*.py             # Python版の実験モジュール群
├── data_recorder.py      # Python版のデータ記録用
├── plot_results.py       # Python版の結果可視化スクリプト
├── data/                 # Python版の出力データ保存先
└── web/                  # Webアプリケーション版 (React + Vite)
    ├── package.json
    ├── index.html
    └── src/
        ├── App.tsx       # Web版のUIエントリーポイント
        ├── config.ts     # Web版の設定ファイル
        ├── audio.ts      # Web Audio API を用いた音声生成モジュール
        └── components/   # 各実験フェーズの画面コンポーネント
```

---

## Web アプリケーション版の実行方法

Webブラウザ上で動作するモダンなUIの実験プログラムです。Node.js がインストールされている環境で実行できます。

### 1. 依存パッケージのインストール
\`\`\`bash
cd web
npm install
\`\`\`

### 2. ローカルサーバーの起動
\`\`\`bash
npm run dev
\`\`\`
起動後、表示される URL（通常は `http://localhost:5173`）にブラウザでアクセスしてください。

### キー操作
- `Space`: 実験の開始・次の試行へ
- `Y` / `N`: Phase 1 で「聴こえた」/「聴こえなかった」
- `C` / `I`: Phase 2 で「連続 (Continuous)」/「途切れ (Interrupted)」

---

## Python デスクトップアプリ版の実行方法

PsychoPy を用いたローカルデスクトップ向けの実験プログラムです。
依存関係の管理には超高速なパッケージマネージャである **[uv](https://github.com/astral-sh/uv)** を使用しています。

### 1. 依存パッケージのインストールと実行環境の構築
\`uv\` がインストールされた環境でリポジトリのルートディレクトリに移動し、以下のコマンドを実行します。

\`\`\`bash
# 依存関係を同期して実行（初回は自動的に仮想環境が作られ、PsychoPy等がインストールされます）
uv run main.py
\`\`\`

または、明示的に仮想環境をアクティベートして実行することも可能です。
\`\`\`bash
uv sync
.venv\Scripts\activate  # Windowsの場合
python main.py
\`\`\`

起動すると PsychoPy ダイアログが表示されますので、Subject ID と ITDリスト（カンマ区切り）を入力して開始してください。
実行中のキー操作は Web版 と同様です (`Y`, `N`, `C`, `I`)。中断する場合は `Escape` キーを押してください。

---

## 設定パラメータ

主要なパラメータの変更は、Python版なら `config.py` を、Web版なら `web/src/config.ts` を編集して行います。

| 定数 | デフォルト値 | 説明 |
|---|---|---|
| `ADAPTIVE_INITIAL_STEP_SIZE`| 6.0 dB | 初期ステップ幅 |
| `ADAPTIVE_SECOND_STEP_SIZE` | 3.0 dB | 2回反転後のステップ幅 |
| `ADAPTIVE_FINAL_STEP_SIZE`  | 0.5 dB | 4回反転後のステップ幅 |
| `ADAPTIVE_MAX_REVERSALS`    | 10 回 | ブロック終了に必要な反転回数 |
| `ADAPTIVE_NUM_REVERSALS_FOR_MEAN` | 6 回 | 閾値計算に用いる反転ポイントの数 |

---

## データ出力と結果の可視化

### Web版のデータ出力
実験の Phase 2 が完了すると、最終的な結果のサマリーが表示され、「Download CSV」ボタンからブラウザ経由で CSV データがダウンロードできます。

### Python版のデータ出力
実験終了後、`data/` フォルダに CSV が自動保存されます。
また、`plot_results.py` が自動的に呼ばれ、階段法の推移グラフと最終閾値のサマリーグラフ（PNG形式）が保存されます。

---

## 参考文献

- Experiment C 仕様 (1-up/1-down staircase method)
