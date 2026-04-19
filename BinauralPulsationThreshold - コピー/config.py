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
PHASE1_STEP_LARGE: float = 4.0      # 初期ステップ幅 (dB)
PHASE1_STEP_SMALL: float = 2.0      # 収束後ステップ幅 (dB)
PHASE1_STEP_CHANGE_REVERSALS: int = 2   # ステップ縮小に必要な反転回数
PHASE1_TOTAL_REVERSALS: int = 8     # Phase1終了に必要な反転回数
PHASE1_MIN_LEVEL: float = -100.0    # 提示レベル下限 (dB FS)
PHASE1_MAX_LEVEL: float = 0.0       # 提示レベル上限 (dB FS)

# ---- Phase 2: 刺激音 ----
MASKER_DURATION: float = 0.165  # マスカー1区間の長さ (秒)
TEST_DURATION: float = 0.165    # テスト信号1区間の長さ (秒)
CROSSFADE_DURATION: float = 0.020   # クロスフェード長さ (秒)
TEST_FREQ: float = 500.0        # テスト信号周波数 (Hz)
SL_OFFSET_DB: float = 65.0      # マスカーレベル = Phase1閾値 + この値 (dB)
# 交番刺激パターン: M-T-M-T-M-T-M (M=4回, T=3回)
N_MASKER: int = 4
N_TEST: int = 3

# ---- Phase 2: Jesteadt適応アルゴリズム ----
TRACK_A_START_LEVEL: float = -10.0  # Track A 開始レベル (マスカーレベルからのオフセット dB)
TRACK_B_START_LEVEL: float = -50.0  # Track B 開始レベル (マスカーレベルからのオフセット dB)
STEP_LARGE: float = 2.0         # 初期ステップ幅 (dB)
STEP_SMALL: float = 1.0         # 収束後ステップ幅 (dB)
STEP_CHANGE_REVERSALS: int = 2  # ステップ縮小に必要な反転回数
TOTAL_REVERSALS: int = 8        # Track終了に必要な反転回数
TEST_MIN_LEVEL: float = -80.0   # テスト信号レベル下限 (dB FS)
TEST_MAX_LEVEL: float = 0.0     # テスト信号レベル上限 (dB FS)

# ---- キー設定 ----
KEY_PHASE1_YES = "y"        # Phase1: 聞こえた（Y キー）
KEY_PHASE1_NO  = "n"        # Phase1: 聞こえなかった（N キー）
KEY_PULSATING = "d"         # Phase2: 断続 Discontinuous
KEY_CONTINUOUS = "c"        # Phase2: 連続 Continuous

# ---- データ保存 ----
DATA_DIR: str = "data"
