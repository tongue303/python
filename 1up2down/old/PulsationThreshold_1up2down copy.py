#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pulsation Threshold 2AFC (1-up/2-down) – Signal Design per Spec
---------------------------------------------------------------
Signal 1 (ターゲット):
  - Alternating pulses: [Tone, Noise, Tone, Noise, Tone, Noise, Tone, Noise, Tone]
  - Each pulse length: 145 ms with 20 ms cosine ramps (rise/fall).
  - Overlap between successive pulses: 20 ms (i.e., onset spacing is 125 ms).
  - Noise pulses: low-pass noise with cutoff fc [Hz], level fixed at -40 dBFS.
  - Tone pulses: pure tone ft [Hz], level Lt [dBFS] (staircased).

Signal 2（比較刺激）:
  - Continuous tone of 1145 ms (20 ms ramps), at ft [Hz], level Lt [dBFS].
  - Add low-pass noise pulses (same shape/cutoff/level as above) starting at onsets:
      125 ms, 375 ms, 625 ms, 875 ms.
  - Each noise pulse is 145 ms with 20 ms ramps.

Common:
  - Sample rate: 44.1 kHz
  - Pre-silence: 500 ms before each interval
  - Interval duration: cover full 1145 ms stimulus (plus padding)
  - Randomized interval order per trial (2AFC)
  - Staircase: 1-up/2-down on Lt. Start step 2 dB; after first reversal, step = 1 dB.
  - Stop after 6 reversals or 60 trials
  - Threshold = mean of last 3 reversal levels (Lt)
  - Logging: trial, condition, response, correct, fc, ft, Lt, timestamp
"""

import csv, math, os, random, sys, time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# Try audio
AUDIO_OK = True
try:
    import numpy as np
    import sounddevice as sd
except Exception:
    AUDIO_OK = False
    np = None
    sd = None

# ---------------- Parameters ----------------
@dataclass
class ExperimentParams:
    sample_rate: int = 44100
    ramp_ms: float = 20.0
    pulse_ms: float = 145.0
    overlap_ms: float = 20.0
    pre_silence_ms: float = 500.0

    fc_hz: float = 4000.0
    ft_hz: float = 1000.0
    noise_level_dbfs: float = -40.0
    Lt_start_dbfs: float = -40.0
    Lt_min_dbfs: float = -80.0
    Lt_max_dbfs: float = -3.0

    step_initial_db: float = 2.0
    step_after_first_reversal_db: float = 1.0
    max_trials: int = 60
    max_reversals: int = 6
    reversals_for_threshold: int = 3

    feedback: bool = True
    response_keys: Tuple[str, str] = ("1", "2")

    FORCE_SIMULATION: bool = False
    sim_threshold_dbfs: float = -28.0
    sim_beta: float = 1.2
    sim_lapse: float = 0.02

    subject_id: str = "S001"
    session_id: str = time.strftime("%Y%m%d")

# Helpers
def db_to_amp(db: float) -> float:
    return 10 ** (db / 20.0)

# OK (25/8/20)
def cosine_ramp(buf: "np.ndarray", ramp_samp: int) -> "np.ndarray":
    if ramp_samp <= 0: return buf
    ramp = 0.5 - 0.5 * np.cos(np.linspace(0, math.pi, ramp_samp))
    env = np.ones_like(buf)
    env[:ramp_samp] *= ramp
    env[-ramp_samp:] *= ramp[::-1]
    return buf * env

def make_tone(duration_s: float, sr: int, freq: float, amp: float, ramp_s: float):
    t = np.arange(int(duration_s * sr)) / sr
    x = np.sin(2 * np.pi * freq * t) * amp
    return cosine_ramp(x, min(int(ramp_s * sr), len(x)//2))

def lowpass_noise(duration_s: float, sr: int, cutoff_hz: float, amp: float, ramp_s: float):
    n = int(duration_s * sr)
    x = np.random.randn(n)
    X = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1.0/sr)
    H = (freqs <= cutoff_hz).astype(float)
    y = np.fft.irfft(X * H, n=n)
    rms = np.sqrt(np.mean(y**2)) + 1e-12
    y = (y / rms) * amp / np.sqrt(2)
    y = cosine_ramp(y, min(int(ramp_s * sr), len(y)//2))
    return y

def play(buf, sr: int):
    sd.play(buf.astype(np.float32), sr, blocking=True)

def prompt_user(prompt: str) -> str:
    sys.stdout.write(prompt); sys.stdout.flush()
    while True:
        ans = sys.stdin.readline().strip().lower()
        if ans: return ans

def ms_to_s(ms: float) -> float: return ms/1000.0

# Build Signal1
def build_signal1(p: ExperimentParams, Lt_dbfs: float) -> "np.ndarray":
    sr = p.sample_rate
    pulse_s = ms_to_s(p.pulse_ms)
    ramp_s = ms_to_s(p.ramp_ms)
    total_s = ms_to_s(1145.0)
    total_samples = int(round(total_s * sr))
    buf = np.zeros(total_samples)
    tone_amp = db_to_amp(Lt_dbfs)
    noise_amp = db_to_amp(p.noise_level_dbfs)

    onsets_ms = [0,125,250,375,500,625,750,875,1000]
    for idx, onset_ms in enumerate(onsets_ms):
        start = int(round(ms_to_s(onset_ms)*sr))
        if idx % 2 == 0:
            pulse = make_tone(pulse_s, sr, p.ft_hz, tone_amp, ramp_s)
        else:
            pulse = lowpass_noise(pulse_s, sr, p.fc_hz, noise_amp, ramp_s)
        end = min(start+len(pulse), total_samples)
        buf[start:end] += pulse[:end-start]
    peak = np.max(np.abs(buf))+1e-12
    if peak>1: buf = buf/peak*0.999
    return buf

# Build Signal2
def build_signal2(p: ExperimentParams, Lt_dbfs: float) -> "np.ndarray":
    sr = p.sample_rate
    total_s = ms_to_s(1145.0)
    ramp_s = ms_to_s(p.ramp_ms)
    tone_amp = db_to_amp(Lt_dbfs)
    base = make_tone(total_s, sr, p.ft_hz, tone_amp, ramp_s)
    pulse_s = ms_to_s(p.pulse_ms)
    noise_amp = db_to_amp(p.noise_level_dbfs)
    for onset_ms in [125,375,625,875]:
        start = int(round(ms_to_s(onset_ms)*sr))
        noise_pulse = lowpass_noise(pulse_s, sr, p.fc_hz, noise_amp, ramp_s)
        end = min(start+len(noise_pulse), len(base))
        base[start:end]+=noise_pulse[:end-start]
    peak = np.max(np.abs(base))+1e-12
    if peak>1: base=base/peak*0.999
    return base

def pad_with_presilence(buf, p: ExperimentParams):
    pre = np.zeros(int(round(ms_to_s(p.pre_silence_ms)*p.sample_rate)))
    return np.concatenate([pre, buf])

# Staircase
@dataclass
class StairState:
    Lt_db: float
    trial_index: int = 0
    reversals: int = 0
    last_direction: Optional[int] = None
    reversal_levels: List[float] = field(default_factory=list)
    consecutive_correct: int = 0
    current_step_db: float = 2.0
    had_first_reversal: bool = False

class OneUpTwoDownLt:
    def __init__(self,p:ExperimentParams):
        start=max(min(p.Lt_start_dbfs,p.Lt_max_dbfs),p.Lt_min_dbfs)
        self.state=StairState(Lt_db=start,current_step_db=p.step_initial_db)
        self.p=p
    def update(self,correct:bool):
        s=self.state; direction=None
        if correct:
            s.consecutive_correct+=1
            if s.consecutive_correct>=2:
                old=s.Lt_db
                s.Lt_db=max(s.Lt_db-s.current_step_db,self.p.Lt_min_dbfs)
                direction=-1; s.consecutive_correct=0
        else:
            s.consecutive_correct=0
            old=s.Lt_db
            s.Lt_db=min(s.Lt_db+s.current_step_db,self.p.Lt_max_dbfs)
            direction=+1
        if direction is not None and s.last_direction is not None and direction!=s.last_direction:
            s.reversals+=1; s.reversal_levels.append(old)
            if not s.had_first_reversal:
                s.had_first_reversal=True
                s.current_step_db=self.p.step_after_first_reversal_db
        if direction is not None: s.last_direction=direction
    def done(self): return self.state.reversals>=self.p.max_reversals or self.state.trial_index>=self.p.max_trials
    def threshold(self):
        if len(self.state.reversal_levels)>=self.p.reversals_for_threshold:
            return sum(self.state.reversal_levels[-self.p.reversals_for_threshold:])/self.p.reversals_for_threshold
        return None

# Simulation
def sim_correct_prob(p,Lt_dbfs):
    gamma=0.5; lapse=p.sim_lapse
    x=10**((Lt_dbfs-p.sim_threshold_dbfs)/20.0)
    pc=gamma+(1-gamma-lapse)*(1-math.exp(-(x**p.sim_beta)))
    return max(min(pc,1),0)
def simulated_response(p,Lt_dbfs,signal_interval:int):
    correct=random.random()<sim_correct_prob(p,Lt_dbfs)
    if correct: return signal_interval,True
    else: return (1 if signal_interval==2 else 2),False

# Trial
def run_trial(p,stair,writer):
    s=stair.state; s.trial_index+=1
    Lt=s.Lt_db
    signal_interval=random.choice([1,2])
    if not AUDIO_OK or p.FORCE_SIMULATION:
        resp_interval,correct=simulated_response(p,Lt,signal_interval)
    else:
        sig1=pad_with_presilence(build_signal1(p,Lt),p)
        sig2=pad_with_presilence(build_signal2(p,Lt),p)
        L=max(len(sig1),len(sig2))
        sig1=np.pad(sig1,(0,L-len(sig1)))
        sig2=np.pad(sig2,(0,L-len(sig2)))
        if signal_interval==1: first,second=sig1,sig2
        else: first,second=sig2,sig1
        print(f"\nTrial {s.trial_index} (Lt={Lt:.2f} dBFS)")
        play(first,p.sample_rate); time.sleep(0.25); play(second,p.sample_rate)
        ans=prompt_user(f"Which interval had the TARGET? {p.response_keys[0]} or {p.response_keys[1]}: ")
        if ans not in p.response_keys: resp_interval=0; correct=False
        else: resp_interval=1 if ans==p.response_keys[0] else 2; correct=(resp_interval==signal_interval)
    if p.feedback: print("✓ Correct!" if correct else "✗ Incorrect.")
    ts=time.strftime("%Y-%m-%d %H:%M:%S")
    writer.writerow([s.trial_index,f"signal_interval={signal_interval}",resp_interval,int(correct),p.fc_hz,p.ft_hz,f"{Lt:.2f}",ts])
    stair.update(correct)
    thr=stair.threshold()
    if thr is not None: print(f"Current threshold estimate: {thr:.2f} dBFS")
    print(f"Next Lt={stair.state.Lt_db:.2f}, reversals={stair.state.reversals}, step={stair.state.current_step_db}")

def main():
    print("=== Pulsation Threshold 2AFC ===")
    p=ExperimentParams()
    outdir="results"; os.makedirs(outdir,exist_ok=True)
    csv_path=os.path.join(outdir,f"pulsation_{p.subject_id}_{p.session_id}_{time.strftime('%H%M%S')}.csv")
    f=open(csv_path,"w",newline="",encoding="utf-8"); writer=csv.writer(f)
    writer.writerow(["trial","condition","response","correct","fc","ft","Lt","timestamp"])
    if AUDIO_OK and not p.FORCE_SIMULATION: print("[Mode] Real audio"); sd.default.samplerate=p.sample_rate
    else: print("[Mode] SIMULATED OBSERVER")
    stair=OneUpTwoDownLt(p)
    try:
        while not stair.done(): run_trial(p,stair,writer)
    except KeyboardInterrupt: print("Aborted")
    finally: f.close()
    thr=stair.threshold()
    print("=== Finished ===")
    print("Log saved:",csv_path)
    if thr: print(f"Estimated threshold: {thr:.2f} dBFS")
    else: print("Not enough reversals")

if __name__=="__main__":
    main()
