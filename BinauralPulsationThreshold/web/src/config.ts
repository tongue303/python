// config.ts
// パルセーション閾値測定プログラム 共通設定ファイル

// ---- 音声基本設定 ----
export const SAMPLE_RATE = 44100; // サンプリングレート (Hz)
export const N_CHANNELS = 2; // ステレオ (左=0, 右=1)

// ---- 刺激音 共通 ----
export const RAMP_DURATION = 0.020; // コサインテーパー長さ (秒)

// ---- Phase 1: 1kHz閾値測定 ----
export const PHASE1_FREQ = 1000.0; // 純音周波数 (Hz)
export const PHASE1_DURATION = 0.500; // 1呈示あたりの長さ (秒)
export const PHASE1_START_LEVEL = -20.0; // 開始レベル (dB FS, フルスケール基準)
export const PHASE1_STEP_LARGE = 2.0; // 初期ステップ幅 (dB)
export const PHASE1_STEP_SMALL = 1.0; // 収束後ステップ幅 (dB)
export const PHASE1_STEP_CHANGE_REVERSALS = 1; // ステップ縮小に必要な反転回数
export const PHASE1_TOTAL_REVERSALS = 4; // Phase1終了に必要な反転回数
export const PHASE1_MIN_LEVEL = -100.0; // 提示レベル下限 (dB FS)
export const PHASE1_MAX_LEVEL = 0.0; // 提示レベル上限 (dB FS)

// ---- Phase 2: 刺激音 ----
export const MASKER_DURATION = 0.145; // マスカー1区間の長さ (秒)
export const TEST_DURATION = 0.145; // テスト信号1区間の長さ (秒)
export const CROSSFADE_DURATION = 0.020; // クロスフェード長さ (秒)
export const TEST_FREQ = 500.0; // テスト信号周波数 (Hz)
export const MOD_FREQ = 250.0; // 変調周波数 (Hz)
export const MOD_TYPE: "None" | "SAM" | "Transposed" = "None"; // 変調タイプ
export const MASKER_ITD_US = 0; // マスカーのITD (µs)
export const TARGET_SL = 40.0; // マスカーの目標SL

// 交番刺激パターン (T-M-T-M-...-S)
export const N_TEST = 5;
export const N_MASKER = N_TEST - 1;
export const N_SILENCE = 1;

// ---- Phase 2: 1-up/1-down 適応法 (Experiment C 準拠) ----
export const ADAPTIVE_INITIAL_STEP_SIZE = 6.0;
export const ADAPTIVE_SECOND_STEP_SIZE = 3.0;
export const ADAPTIVE_FINAL_STEP_SIZE = 0.5;
export const ADAPTIVE_REVERSAL_TRIGGER_1 = 2;
export const ADAPTIVE_REVERSAL_TRIGGER_2 = 4;
export const ADAPTIVE_MAX_REVERSALS = 10;
export const ADAPTIVE_NUM_REVERSALS_FOR_MEAN = 6;
export const ADAPTIVE_INITIAL_TARGET_OFFSET = 20.0;
export const ADAPTIVE_ROVING_RANGE = 3.0;

export const TEST_MIN_LEVEL = -80.0;
export const TEST_MAX_LEVEL = 0.0;

// ---- キー設定 ----
export const KEY_PHASE1_YES = "y";
export const KEY_PHASE1_NO = "n";
export const KEY_CONTINUOUS = "c";
export const KEY_INTERRUPTED = "i";

// ---- 教示文 ----
export const INSTRUCTION_TEXT = `====== Instructions ======
In this experiment, we will measure your pulsation threshold.

[ Phase 1 ]
We will measure the minimum volume at which you can hear a 1000Hz pure tone.
Press the '${KEY_PHASE1_YES.toUpperCase()}' key if you heard the sound.
Press the '${KEY_PHASE1_NO.toUpperCase()}' key if you did not hear it.

[ Phase 2 ]
First, you will hear a clear, continuous reference tone.
Following a brief silence, you will hear an alternating pattern of noise and a test tone.
Using the first tone as a reference, please judge how the test tone in the alternating pattern sounded to you:
Press the '${KEY_CONTINUOUS.toUpperCase()}' key if the test tone sounded "continuous" between the noise bursts.
Press the '${KEY_INTERRUPTED.toUpperCase()}' key if it sounded "interrupted".

Press the [Space] key to begin when you are ready.`;
