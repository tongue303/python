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
MASKER_DURATION: float = 0.165  # マスカー1区間の長さ (秒)
TEST_DURATION: float = 0.165    # テスト信号1区間の長さ (秒)
CROSSFADE_DURATION: float = 0.020   # クロスフェード長さ (秒)
TEST_FREQ: float = 500.0        # テスト信号周波数 (Hz)
MOD_FREQ: float = 250.0         # 変調周波数 (Hz)
MOD_TYPE: str = "None"    # 変調タイプ ("None", "SAM", "Transposed")
MASKER_ITD_US: int = 0          # マスカーのITD (µs)
SL_OFFSET_DB: float = 50.0      # マスカーレベル = Phase1閾値 + この値 (dB)
# 交番刺激パターン: M-T-M-T-M-T-M (M=4回, T=3回)
N_MASKER: int = 4
N_TEST: int = 3

# ---- Phase 2: Jesteadt適応アルゴリズム ----
TRACK_A_START_LEVEL: float = 10.0  # Track A 開始レベル (マスカーレベルからのオフセット dB)
TRACK_B_START_LEVEL: float = -20.0  # Track B 開始レベル (マスカーレベルからのオフセット dB)
STEP_LARGE: float = 2.0         # 初期ステップ幅 (dB)
STEP_SMALL: float = 1.0         # 収束後ステップ幅 (dB)
STEP_CHANGE_REVERSALS: int = 1  # ステップ縮小に必要な反転回数
TOTAL_REVERSALS: int = 4        # Track終了に必要な反転回数
TEST_MIN_LEVEL: float = -80.0   # テスト信号レベル下限 (dB FS)
TEST_MAX_LEVEL: float = 0.0     # テスト信号レベル上限 (dB FS)

# ---- キー設定 ----
KEY_PHASE1_YES = "y"        # Phase1: 聞こえた（Y キー）
KEY_PHASE1_NO  = "n"        # Phase1: 聞こえなかった（N キー）
KEY_PULSATING = "d"         # Phase2: 断続 Discontinuous
KEY_CONTINUOUS = "c"        # Phase2: 連続 Continuous

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
    "ノイズ（ジャージャー音）とテスト音（ピー音や変調音）が交互に鳴ります。\n"
    "テスト音が途切れず「連続」して聞こえる場合は '{KEY_C}' キーを、\n"
    "テスト音がノイズの間に「断続」して聞こえる場合は '{KEY_D}' キーを押してください。\n\n"
    "準備ができたら [Space] キーを押して開始してください。"
).format(
    KEY_YES=KEY_PHASE1_YES.upper(),
    KEY_NO=KEY_PHASE1_NO.upper(),
    KEY_C=KEY_CONTINUOUS.upper(),
    KEY_D=KEY_PULSATING.upper()
)
