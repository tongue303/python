# -*- coding: utf-8 -*-
"""
phase2_adjustment.py
====================
Phase 2: 調整法（Method of Adjustment）

被験者が自らテスト信号の音量を調整し、パルセーション閾値（連続して聞こえ始める境界）
を決定する。
"""

import numpy as np
from psychopy import visual, sound, core, event

import config
from phase2_stimulus import build_alternating_stimulus


def run_adjustment_condition(
    win: visual.Window,
    masker_spectrum_level_db: float,
    itd_seconds: float,
    subject_id: str,
    itd_label_us: int,
    sl_reference_db: float,
    test_freq: float,
    mod_freq: float,
    mod_type: str,
    masker_itd_sec: float,
    masker_itd_us: int,
) -> float:
    """
    調整法（Method of Adjustment）による1つのITD条件の実行

    Parameters
    ----------
    win : psychopy.visual.Window
    masker_spectrum_level_db : float
        マスカーのスペクトルレベル (dB/Hz)。
    itd_seconds : float
        ITD (秒)。
    subject_id : str
    itd_label_us : int
    sl_reference_db : float
    test_freq : float
    mod_freq : float
    mod_type : str
    masker_itd_sec : float
    masker_itd_us : int

    Returns
    -------
    threshold_db : float
        被験者が最終的に決定した閾値 (dB FS)。
    """
    # ── 教示画面 ──
    instr = visual.TextStim(
        win,
        text=(
            f"ITD = {itd_label_us} µs\n\n"
            "矢印キー（↑ / ↓）でテスト音の音量を調整してください。\n"
            "ノイズの間で途切れることなく「連続」して聞こえる境界を見つけたら\n"
            "[Enter] を押して決定します。\n\n"
            "[スペース] で開始"
        ),
        height=0.06, wrapWidth=1.5, color="white",
    )
    instr.draw()
    win.flip()
    event.waitKeys(keyList=["space"])

    prompt = visual.TextStim(win, text="", height=0.08, color="white")
    
    current_level = masker_spectrum_level_db + config.ADJUSTMENT_START_LEVEL
    step = config.ADJUSTMENT_STEP

    while True:
        current_level = float(np.clip(current_level, config.TEST_MIN_LEVEL, config.TEST_MAX_LEVEL))
        
        # ── 刺激生成 ──
        stim_array = build_alternating_stimulus(
            masker_spectrum_level_db, current_level, itd_seconds,
            test_freq=test_freq, mod_freq=mod_freq, mod_type=mod_type, masker_itd_sec=masker_itd_sec
        )
        snd = sound.Sound(
            value=stim_array,
            sampleRate=config.SAMPLE_RATE,
            stereo=True,
        )

        prompt.text = f"音量調整中...\n[↑] 上げる  [↓] 下げる\n[Enter] 決定"
        prompt.draw()
        win.flip()

        event.clearEvents()
        snd.play()
        
        stim_duration = stim_array.shape[0] / config.SAMPLE_RATE
        start_time = core.getTime()
        
        registered = False
        
        # 刺激再生中はキー入力を監視する（終了するまで待機）
        last_key_time = 0.0
        while core.getTime() - start_time < stim_duration:
            keys = event.getKeys(keyList=[config.KEY_UP, config.KEY_DOWN, config.KEY_REGISTER, "escape"])
            for key in keys:
                if key == "escape":
                    snd.stop()
                    win.close()
                    core.quit()
                elif key == config.KEY_REGISTER:
                    registered = True
                else:
                    # キーリピート（長押し）による音量暴走を防ぐため、150msのデバウンスを設ける
                    now = core.getTime()
                    if now - last_key_time > 0.15:
                        if key == config.KEY_UP:
                            current_level += step
                        elif key == config.KEY_DOWN:
                            current_level -= step
                        last_key_time = now
            core.wait(0.01)
            
        snd.stop()
        snd = None  # 明示的に解放してオーディオバッファの残留を防ぐ

        if registered:
            break
            
        # 短インターバル
        core.wait(0.1)

    return current_level

if __name__ == "__main__":
    import sys
    print("This module is not intended to be run directly. Use main.py.")
