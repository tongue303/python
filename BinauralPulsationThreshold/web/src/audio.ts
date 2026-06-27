import * as config from "./config";

// --- ユーティリティ関数 ---

/** 両端にコサインテーパーを適用する（in-place） */
export function applyCosineRamp(wave: Float32Array, sr: number, rampSec: number): void {
  const rampN = Math.floor(sr * rampSec);
  if (rampN === 0) return;
  for (let i = 0; i < rampN; i++) {
    const ramp = 0.5 * (1 - Math.cos((Math.PI * i) / rampN));
    wave[i] *= ramp;
    wave[wave.length - 1 - i] *= ramp;
  }
}

/** RMSを計算して正規化（in-place） */
export function rmsNormalize(wave: Float32Array, targetRms: number = 1.0): void {
  let sumSq = 0;
  for (let i = 0; i < wave.length; i++) {
    sumSq += wave[i] * wave[i];
  }
  const rms = Math.sqrt(sumSq / wave.length);
  if (rms < 1e-10) return;
  const factor = targetRms / rms;
  for (let i = 0; i < wave.length; i++) {
    wave[i] *= factor;
  }
}

/** dB FS を振幅に変換 */
export function dbToAmplitude(levelDbFs: number): number {
  return Math.pow(10, levelDbFs / 20.0);
}

// --- 音声生成関数 ---

/**
 * 帯域通過ホワイトノイズを生成し、ITDを付与してステレオ化する。
 * Web Audio API (OfflineAudioContext) を使用してフィルタリングする。
 */
export async function generateBandpassNoise(
  levelDbFs: number,
  centerFreq: number,
  itdSeconds: number = 0.0,
  duration: number = config.MASKER_DURATION
): Promise<[Float32Array, Float32Array]> {
  const sr = config.SAMPLE_RATE;
  const baseN = Math.floor(sr * duration);
  const shiftN = Math.floor(Math.round(Math.abs(itdSeconds) * sr));
  const totalN = baseN + shiftN;

  // バタワース4次相当の特性を完全に模倣するのは難しいが、
  // BiquadFilterのbandpassを使って近似する。Qの計算:
  // 通過帯域は fc/sqrt(2) ~ fc*sqrt(2)
  const q = Math.sqrt(2); // おおよその1オクターブ幅のQ値

  const offlineCtx = new OfflineAudioContext(1, totalN, sr);
  const noiseBuffer = offlineCtx.createBuffer(1, totalN, sr);
  const noiseData = noiseBuffer.getChannelData(0);
  for (let i = 0; i < totalN; i++) {
    // 正規分布に近いノイズを近似生成（中心極限定理）
    let rand = 0;
    for (let j = 0; j < 6; j++) rand += Math.random();
    noiseData[i] = (rand - 3) / 3;
  }

  const source = offlineCtx.createBufferSource();
  source.buffer = noiseBuffer;

  const filter1 = offlineCtx.createBiquadFilter();
  filter1.type = "bandpass";
  filter1.frequency.value = centerFreq;
  filter1.Q.value = q;

  const filter2 = offlineCtx.createBiquadFilter();
  filter2.type = "bandpass";
  filter2.frequency.value = centerFreq;
  filter2.Q.value = q;

  // 4次相当（12dB/oct x 2 = 24dB/oct）の急峻さにするため直列に接続
  source.connect(filter1);
  filter1.connect(filter2);
  filter2.connect(offlineCtx.destination);

  source.start();
  const renderedBuffer = await offlineCtx.startRendering();
  const filtered = renderedBuffer.getChannelData(0);

  // 全体をRMS正規化
  rmsNormalize(filtered, 1.0);
  const amplitude = dbToAmplitude(levelDbFs);
  for (let i = 0; i < totalN; i++) {
    filtered[i] *= amplitude;
  }

  // 左右切り出しによるITD付与
  const left = new Float32Array(baseN);
  const right = new Float32Array(baseN);

  if (itdSeconds >= 0) {
    right.set(filtered.subarray(0, baseN));
    left.set(filtered.subarray(shiftN, shiftN + baseN));
  } else {
    left.set(filtered.subarray(0, baseN));
    right.set(filtered.subarray(shiftN, shiftN + baseN));
  }

  applyCosineRamp(left, sr, config.RAMP_DURATION);
  applyCosineRamp(right, sr, config.RAMP_DURATION);

  return [left, right];
}

/**
 * テスト信号（純音、SAM、Transposed）を生成しITDを付与する。
 */
export function generateTestSignal(
  levelDbFs: number,
  itdSeconds: number,
  duration: number = config.TEST_DURATION,
  testFreq: number = config.TEST_FREQ,
  modFreq: number = config.MOD_FREQ,
  modType: string = "None"
): [Float32Array, Float32Array] {
  const sr = config.SAMPLE_RATE;
  const baseN = Math.floor(sr * duration);
  const shiftN = Math.floor(Math.round(Math.abs(itdSeconds) * sr));
  const totalN = baseN + shiftN;

  const signal = new Float32Array(totalN);
  for (let i = 0; i < totalN; i++) {
    const t = i / sr;
    const carrier = Math.sin(2 * Math.PI * testFreq * t);
    let envelope = 1.0;

    if (testFreq >= 1500.0 && modType !== "None") {
      if (modType === "SAM") {
        envelope = 1.0 - Math.cos(2 * Math.PI * modFreq * t);
      } else if (modType === "Transposed") {
        envelope = Math.max(0, Math.cos(2 * Math.PI * modFreq * t));
      }
    }
    signal[i] = carrier * envelope;
  }

  rmsNormalize(signal, 1.0);
  const amplitude = dbToAmplitude(levelDbFs);

  const left = new Float32Array(baseN);
  const right = new Float32Array(baseN);

  if (itdSeconds >= 0) {
    right.set(signal.subarray(0, baseN));
    left.set(signal.subarray(shiftN, shiftN + baseN));
  } else {
    left.set(signal.subarray(0, baseN));
    right.set(signal.subarray(shiftN, shiftN + baseN));
  }

  for (let i = 0; i < baseN; i++) {
    left[i] *= amplitude;
    right[i] *= amplitude;
  }

  applyCosineRamp(left, sr, config.RAMP_DURATION);
  applyCosineRamp(right, sr, config.RAMP_DURATION);

  return [left, right];
}

/**
 * T-M-T-M-T-M-T-S の交番刺激を合成する。
 * AudioBufferを返す。
 */
export async function buildAlternatingStimulus(
  maskerSpectrumLevelDb: number,
  testLevelDb: number,
  testItdSeconds: number,
  testFreq: number = config.TEST_FREQ,
  modFreq: number = config.MOD_FREQ,
  modType: string = "None",
  maskerItdSec: number = 0.0
): Promise<AudioBuffer> {
  const sr = config.SAMPLE_RATE;
  const cfN = Math.floor(sr * config.CROSSFADE_DURATION);

  // マスカー全体のレベル計算
  const bandwidth = testFreq * Math.sqrt(2) - testFreq / Math.sqrt(2);
  const overallMaskerDb = maskerSpectrumLevelDb + 10 * Math.log10(bandwidth);

  const numContinuousT = 2 * config.N_TEST - 1;
  const numSilence = 2 * config.N_SILENCE;
  const numAlternating = 2 * config.N_TEST;
  const totalSegments = numContinuousT + numSilence + numAlternating;

  const testSeg = generateTestSignal(testLevelDb, testItdSeconds, config.TEST_DURATION, testFreq, modFreq, modType);
  const segN = testSeg[0].length;
  const totalN = segN * totalSegments - cfN * (totalSegments - 1);

  const outLeft = new Float32Array(totalN);
  const outRight = new Float32Array(totalN);

  let pos = 0;

  // 1. 参照用連続音 (T)
  // 単純なクロスフェード連結による位相干渉（音の途切れ）を防ぐため、1つの長い波形として生成する。
  const continuousDuration = numContinuousT * config.TEST_DURATION - (numContinuousT - 1) * config.CROSSFADE_DURATION;
  const longTestSeg = generateTestSignal(testLevelDb, testItdSeconds, continuousDuration, testFreq, modFreq, modType);
  const longTestSegN = longTestSeg[0].length;

  for (let j = 0; j < longTestSegN; j++) {
    outLeft[pos + j] += longTestSeg[0][j];
    outRight[pos + j] += longTestSeg[1][j];
  }
  pos += longTestSegN - cfN;

  // 2. 無音 (S)
  const silenceDuration = numSilence * config.TEST_DURATION - (numSilence - 1) * config.CROSSFADE_DURATION;
  const silenceN = Math.floor(sr * silenceDuration);
  pos += silenceN - cfN; // 何も足さずに位置だけ進める

  // 3. 交番パターン (T-M-T-M-...-S)
  for (let i = 0; i < numAlternating; i++) {
    let segLeft: Float32Array;
    let segRight: Float32Array;

    if (i === numAlternating - 1) {
      // 無音
      segLeft = new Float32Array(segN);
      segRight = new Float32Array(segN);
    } else if (i % 2 === 0) {
      // テスト信号
      segLeft = testSeg[0];
      segRight = testSeg[1];
    } else {
      // マスカー
      const maskerSeg = await generateBandpassNoise(overallMaskerDb, testFreq, maskerItdSec, config.MASKER_DURATION);
      segLeft = maskerSeg[0];
      segRight = maskerSeg[1];
    }

    for (let j = 0; j < segN; j++) {
      outLeft[pos + j] += segLeft[j];
      outRight[pos + j] += segRight[j];
    }

    pos += segN - cfN;
  }

  // クリップチェック
  let maxAmp = 0;
  for (let i = 0; i < totalN; i++) {
    maxAmp = Math.max(maxAmp, Math.abs(outLeft[i]), Math.abs(outRight[i]));
  }
  if (maxAmp > 0.99) {
    throw new Error(
      "The generated stimulus amplitude exceeded the clipping threshold (1.0).\n" +
      "The Reference SL (Phase 1 threshold) or the Target SL may be too high.\n" +
      "Please lower the PC output volume and increase the amplifier gain."
    );
  }

  // AudioBuffer化
  const ctx = new OfflineAudioContext(2, totalN, sr);
  const buffer = ctx.createBuffer(2, totalN, sr);
  buffer.copyToChannel(outLeft, 0);
  buffer.copyToChannel(outRight, 1);
  return buffer;
}
