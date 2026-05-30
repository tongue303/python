# -*- coding: utf-8 -*-
"""
config.py
=========
パルセーション閾値測定プログラム 共通設定ファイル
全スクリプトから import して使用する。
"""

# ---- 音声基本設定 ----
SAMPLE_RATE: int = 44100        # サンプリングレート (Hz)
N_CHANNELS: int = 2             # ステレオ (左=0, 右=1)

# ---- 刺激音 共通 ----
RAMP_DURATION: float = 0.020    # コサインテーパー長さ (秒)

# ---- Phase 1: 1kHz閾値測定 ----
PHASE1_FREQ: float = 1000.0     # 純音周波数 (Hz)
PHASE1_DURATION: float = 0.500  # 1呈示あたりの長さ (秒)
PHASE1_START_LEVEL: float = -20.0   # 開始レベル (dB FS, フルスケール基準)
PHASE1_STEP_LARGE: float = 2.0      # 初期ステップ幅 (dB)
PHASE1_STEP_SMALL: float = 1.0      # 収束後ステップ幅 (dB)
PHASE1_STEP_CHANGE_REVERSALS: int = 1   # ステップ縮小に必要な反転回数
PHASE1_TOTAL_REVERSALS: int = 4     # Phase1終了に必要な反転回数
PHASE1_MIN_LEVEL: float = -100.0    # 提示レベル下限 (dB FS)
PHASE1_MAX_LEVEL: float = 0.0       # 提示レベル上限 (dB FS)

# ---- Phase 2: 刺激音 ----
MASKER_DURATION: float = 0.145  # マスカー1区間の長さ (秒)
TEST_DURATION: float = 0.145    # テスト信号1区間の長さ (秒)
CROSSFADE_DURATION: float = 0.020   # クロスフェード長さ (秒)
TEST_FREQ: float = 500.0        # テスト信号周波数 (Hz)
MOD_FREQ: float = 250.0         # 変調周波数 (Hz)
MOD_TYPE: str = "None"    # 変調タイプ ("None", "SAM", "Transposed")
MASKER_ITD_US: int = 0          # マスカーのITD (µs)
TARGET_SL: float = 40.0         # マスカーの目標SL (Sensation Level または Stimulus Level)
# 交番刺激パターン: T-M-T-M-T-M-T-S (T=4回, M=3回, S=1回)
N_MASKER: int = 3
N_TEST: int = 4
N_SILENCE: int = 1

# ---- Phase 2: 調整法（Method of Adjustment） ----
ADJUSTMENT_START_LEVEL: float =  10.0  # 開始レベル (マスカーレベルからのオフセット dB)
ADJUSTMENT_STEP: float = 1.0           # 1回のキー入力での音量変化ステップ (dB)
TEST_MIN_LEVEL: float = -80.0   # テスト信号レベル下限 (dB FS)
TEST_MAX_LEVEL: float = 0.0     # テスト信号レベル上限 (dB FS)

# ---- キー設定 ----
KEY_PHASE1_YES = "y"        # Phase1: 聞こえた
KEY_PHASE1_NO  = "n"        # Phase1: 聞こえなかった
KEY_UP = "up"               # Phase2: 音量を上げる
KEY_DOWN = "down"           # Phase2: 音量を下げる
KEY_REGISTER = "return"     # Phase2: 決定（登録）

# ---- データ保存 ----
DATA_DIR: str = "data"

# ---- 教示文 ----
INSTRUCTION_TEXT = (
    "====== 全体説明 ======\n"
    "この実験ではパルセーション閾値の測定を行います。\n\n"
    "[ Phase 1 ]\n"
    "1000Hzの純音が聞こえる最小の音の大きさを測定します。\n"
    "音が聞こえたら '{KEY_YES}' キーを、\n"
    "聞こえなかったら '{KEY_NO}' キーを押してください。\n\n"
    "[ Phase 2 ]\n"
    "ノイズ（ジャージャー音）とテスト音が交互に鳴るパターンが繰り返されます。\n"
    "上下の矢印キー（↑ / ↓）を押すと、テスト音の大きさが変わります。\n"
    "テスト音がノイズの間で途切れず「連続」して聞こえる境界（パルセーション閾値）\n"
    "になるように音量を調整してください。\n"
    "見つけたら [Enter] キーを押して登録し、次の条件に進みます。\n\n"
    "準備ができたら [Space] キーを押して開始してください。"
).format(
    KEY_YES=KEY_PHASE1_YES.upper(),
    KEY_NO=KEY_PHASE1_NO.upper(),
)
