import * as config from "./config";

// --- Phase 1: 2-down 1-up (1kHz 聴取閾値測定) ---

export class Phase1ThresholdTrack {
  public currentLevel: number;
  public stepSize: number;
  public consecutiveCorrect: number = 0;
  public nReversals: number = 0;
  public lastDirection: "up" | "down" | null = null;
  public reversalLevels: number[] = [];
  public finished: boolean = false;

  constructor() {
    this.currentLevel = config.PHASE1_START_LEVEL;
    this.stepSize = config.PHASE1_STEP_LARGE;
  }

  public isFinished(): boolean {
    return this.finished;
  }

  public getCurrentLevel(): number {
    return this.currentLevel;
  }

  public getThreshold(): number {
    // ステップ縮小後の反転点のみを使用
    const smallStepReversals = this.reversalLevels.slice(config.PHASE1_STEP_CHANGE_REVERSALS);
    if (smallStepReversals.length > 0) {
      return smallStepReversals.reduce((a, b) => a + b, 0) / smallStepReversals.length;
    }
    if (this.reversalLevels.length > 0) {
      return this.reversalLevels.reduce((a, b) => a + b, 0) / this.reversalLevels.length;
    }
    return this.currentLevel;
  }

  public recordResponse(responded: boolean): void {
    if (responded) {
      // 正答
      this.consecutiveCorrect++;
      if (this.consecutiveCorrect >= 2) {
        if (this.lastDirection === "up") {
          this.nReversals++;
          this.reversalLevels.push(this.currentLevel);
          if (this.nReversals === config.PHASE1_STEP_CHANGE_REVERSALS) {
            this.stepSize = config.PHASE1_STEP_SMALL;
          }
        }
        this.currentLevel -= this.stepSize;
        this.lastDirection = "down";
        this.consecutiveCorrect = 0;
      }
    } else {
      // 誤答
      this.consecutiveCorrect = 0;
      if (this.lastDirection === "down") {
        this.nReversals++;
        this.reversalLevels.push(this.currentLevel);
        if (this.nReversals === config.PHASE1_STEP_CHANGE_REVERSALS) {
          this.stepSize = config.PHASE1_STEP_SMALL;
        }
      }
      this.currentLevel += this.stepSize;
      this.lastDirection = "up";
    }

    // レベル境界チェック
    if (this.currentLevel < config.PHASE1_MIN_LEVEL) {
      this.currentLevel = config.PHASE1_MIN_LEVEL;
      this.lastDirection = "up";
      this.consecutiveCorrect = 0;
    } else if (this.currentLevel > config.PHASE1_MAX_LEVEL) {
      this.currentLevel = config.PHASE1_MAX_LEVEL;
      this.lastDirection = "down";
      this.consecutiveCorrect = 0;
    }

    if (this.nReversals >= config.PHASE1_TOTAL_REVERSALS) {
      this.finished = true;
    }
  }
}

// --- Phase 2: 1-up 1-down (パルセーション閾値測定) ---

export interface TrackHistoryRecord {
  trialGlobal: number;
  levelDb: number;
  response: "continuous" | "interrupted";
  isReversal: boolean;
  reversalCount: number;
  stepSize: number;
}

export class AdaptiveTrack1Up1Down {
  public currentTargetLevel: number;
  public currentStepSize: number;
  public reversalCount: number = 0;
  public previousDirection: 1 | -1 | null = null;
  public reversalLevels: number[] = [];
  public history: TrackHistoryRecord[] = [];
  public trialNo: number = 0;
  public finished: boolean = false;

  constructor(public maskerSpectrumLevelDb: number) {
    const jitter = (Math.random() * 2 - 1) * config.ADAPTIVE_ROVING_RANGE; // -range to +range
    const initialTargetLevel = maskerSpectrumLevelDb + config.ADAPTIVE_INITIAL_TARGET_OFFSET + jitter;

    this.currentTargetLevel = Math.max(
      config.TEST_MIN_LEVEL,
      Math.min(config.TEST_MAX_LEVEL, initialTargetLevel)
    );
    this.currentStepSize = config.ADAPTIVE_INITIAL_STEP_SIZE;
  }

  public isFinished(): boolean {
    return this.finished;
  }

  public getCurrentLevel(): number {
    return this.currentTargetLevel;
  }

  public getThreshold(): number {
    if (this.reversalLevels.length < config.ADAPTIVE_MAX_REVERSALS) {
      return this.reversalLevels.length > 0
        ? this.reversalLevels.reduce((a, b) => a + b, 0) / this.reversalLevels.length
        : this.currentTargetLevel;
    }

    const startIdx = config.ADAPTIVE_MAX_REVERSALS - config.ADAPTIVE_NUM_REVERSALS_FOR_MEAN;
    const targetRevs = this.reversalLevels.slice(startIdx);
    return targetRevs.reduce((a, b) => a + b, 0) / targetRevs.length;
  }

  public recordResponse(isContinuous: boolean, trialGlobal: number): void {
    this.trialNo++;
    let isReversal = false;
    let currentDirection: 1 | -1 = 1;

    if (isContinuous) {
      currentDirection = 1; // UP
    } else {
      currentDirection = -1; // DOWN
    }

    const nextTargetLevel = this.currentTargetLevel + currentDirection * this.currentStepSize;

    // 反転判定
    if (this.previousDirection !== null && currentDirection !== this.previousDirection) {
      this.reversalCount++;
      this.reversalLevels.push(this.currentTargetLevel);
      isReversal = true;

      // ステップサイズ更新
      if (this.reversalCount === config.ADAPTIVE_REVERSAL_TRIGGER_1) {
        this.currentStepSize = config.ADAPTIVE_SECOND_STEP_SIZE;
      } else if (this.reversalCount === config.ADAPTIVE_REVERSAL_TRIGGER_2) {
        this.currentStepSize = config.ADAPTIVE_FINAL_STEP_SIZE;
      }
    }

    // 履歴記録
    this.history.push({
      trialGlobal,
      levelDb: this.currentTargetLevel,
      response: isContinuous ? "continuous" : "interrupted",
      isReversal,
      reversalCount: this.reversalCount,
      stepSize: this.currentStepSize,
    });

    this.previousDirection = currentDirection;

    // 終了判定
    if (this.reversalCount >= config.ADAPTIVE_MAX_REVERSALS) {
      this.finished = true;
    } else {
      this.currentTargetLevel = Math.max(
        config.TEST_MIN_LEVEL,
        Math.min(config.TEST_MAX_LEVEL, nextTargetLevel)
      );
    }
  }
}
