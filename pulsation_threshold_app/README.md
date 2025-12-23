# Pulsation Threshold Experiment App

本プロジェクトは、Plack and Oxenham (2000) による「脈動閾値（Pulsation Threshold）を用いた基底膜非線形性の推定」実験を Python で実装するものです。

## 1. プロジェクト概要
基底膜（BM）の圧縮特性を心理物理学的に測定するため、シグナル音とマスカー音を交互に提示し、シグナルが「断続的（pulsed）」から「連続的（continuous）」に聞こえ方が変化する閾値を測定します。

将来的なWebアプリ化を見据え、刺激生成ロジック、実験制御アルゴリズム、およびユーザーインターフェースを分離したオブジェクト指向設計を採用しています。

## 2. 設計指針
* **Webアプリ対応**: ロジックを `core` パッケージに集約し、FastAPI 等の API サーバーから呼び出し可能な構成とする。
* **刺激の柔軟な差し替え**: 抽象クラス `Stimulus` を継承することで、将来的に正弦波以外の刺激（ノイズ等）にも容易に対応可能とする。
* **事前測定の統合**: 本実験の前に、被験者の聴覚特性およびデバイス特性に合わせた可聴閾値（Absolute Threshold）の測定プロセスを組み込む。

## 3. ディレクトリ構成

```text
pulsation_threshold_app/
├── README.md               # 本ファイル
├── main.py                 # エントリーポイント（SessionManagerの実行）
├── core/                   # 実験の核となるロジック
│   ├── __init__.py
│   ├── stimulus.py         # 刺激生成（正弦波、ランプ、シーケンス合成）
│   ├── adaptive.py         # 適応法アルゴリズム（interleaved staircase）
│   └── experiment.py       # 実験フロー管理（可聴閾値測定 / 本実験）
├── tests/                  # 検証・テスト用ディレクトリ（追加）
│   └── verify_stimulus.py  # ← ここにプロット用プログラムを置く
├── utils/                  # ユーティリティ
│   └── audio.py            # 音声再生・デバイス制御・キャリブレーション
└── data/                   # 測定データ保存用（CSV/JSON）