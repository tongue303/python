# Binaural Pulsation Threshold Modifications

## Goal Description
BinauralPulsationThreshold プログラムに対して、以下の変更を行います。
1. **1 kHz Hearing Thresholdの保存**: 取得したSL基準値(1kHzの聴取閾値)をCSVデータに保存する。
2. **Phase 2結果の校正**: 結果プロット時(plot_results.py)に、1kHz Hearing Thresholdを基準とした値(dB SL in 1 kHz)になるようにY軸を調整・表示する。
3. **回答時間制限の撤廃**: Phase 2の交互刺激提示後、被験者が「連続」または「断続」と回答するまで待機し、回答入力後に次の刺激へ進むようにする。
4. **テスト音周波数・変調タイプの選択機能**: 初期ダイアログでテスト音の周波数、および変調周波数(Modulation Frequency)を指定できるようにする。1.5kHz以上の場合は振幅変調として「Sinusoidal Amplitude Modulation (SAM)」か「Transposed Stimuli」を選択できるようにする。
    - **ITDの適用方法について**: 搬送波（キャリア）に変調波（エンベロープ）を掛け合わせた後の最終的な信号に対して、全体にITD（時間遅延）を適用する。
5. **教示文の追加**: 最初のプログラム立ち上げ時に、実験の全体的な説明やPhase1/2に関する教示文を表示する画面を追加する。
6. **マスカーITDの追加選択**: 初期ダイアログにマスカーのITD（0μs, 1000μsなど）を設定できるようにする。
7. **サウンドデバイスの選択機能**: プログラム実行時の初期ダイアログで、使用するオーディオ出力デバイスを一覧から選択できるようにする。

## Proposed Changes

### config.py
- [NEW] 変調関連およびマスカーITD関連のデフォルト値: `TEST_FREQ: float = 500.0`, `MOD_FREQ: float = 250.0`, `MOD_TYPE: str = "None"`, `MASKER_ITD_US: int = 0` (これらはGUIで上書きされるが、デフォルト値として定義)。
- [NEW] 教示文表示用のテキストやキー設定を追加。

### main.py
- [NEW] `show_instructions(win)` 関数を作成し、Phase1開始前の最初の画面として教示文を表示する。
- [MODIFY] `show_dialog()` に `Test frequency (Hz)`, `Modulation frequency (Hz)`, `Modulation type (SAM, Transposed, None)`, `Masker ITD (us)` に加え、新たに利用可能な **サウンドデバイス一覧の選択（ドロップダウン）** フィールドを追加。`psychopy.sound.getDevices()` 等でデバイス名を取得し、選択肢にセットする。
- [MODIFY] 取得したデバイス情報を PsychoPy の設定 (`psychopy.prefs.hardware['audioDevice']` 等) に反映するか、`Sound` オブジェクト生成時に指定する。
- [MODIFY] 取得したパラメータ群を `run_itd_condition` に渡す。
- [MODIFY] `recorder.add_trial` に渡す引数として、CSVに記録するためにダイアログで取得したパラメータ（`test_freq`, `mod_freq`, `mod_type`, `masker_itd`）も引き回す。
- [MODIFY] マスカーITDの値を秒に変換し、刺激生成ルーチンに渡す。

### data_recorder.py
- [MODIFY] `DataRecorder.FIELDNAMES` に `"sl_reference_db"`, `"test_freq"`, `"mod_freq"`, `"mod_type"`, `"masker_itd_us"` を追加。
- [MODIFY] `add_trial()` にこれらの引数を追加し、各試行のデータとして保存。

### phase2_adaptive.py
- [MODIFY] `event.waitKeys()` から `maxWait=3.0` を削除し、無限待機に変更。
- [MODIFY] タイムアウト時のフォールバック処理を削除。
- [MODIFY] `run_itd_condition` の引数に新パラメータを追加し、`build_alternating_stimulus` および `recorder.add_trial` に渡す。

### phase2_stimulus.py
- [MODIFY] `generate_pink_noise` 関数に ITD パラメータ (`itd_seconds`) を追加し、ピンクノイズに対して時間遅延成分を付与する。通常、片耳を遅延させる形でステレオ波形を生成（左右で位相をずらしたノイズとなるか確認。あるいは左右別で生成）。→ **ピンクノイズのITDの厳密な定義：生成したノイズを左右で指定時間分シフトするか、あるいはFFTの位相をずらすことで実現。ここではシンプルに時間シフト(Zero-padding/スライシング)を行うか、FFT位相シフトで実装する。**
- [MODIFY] `generate_test_signal` (または新設関数) で、1.5kHz以上かつ変調ありの場合は：
  - キャリア成分（単一正弦波）を生成。
  - エンベロープ成分（SAM または Transposed）を生成。
  - キャリアとエンベロープを乗算してモノラル波形とする。
  - 生成したモノラル波形に対して、ITD（時間遅延）を適用してステレオ波形にする（例：右チャンネルを遅延させるなど）。純音（500Hz等）の際と同様に、FFT位相シフトか実時間シフトを使用する。既存の `phase_delay_rad` による処理は周波数固有の位相遅延となるため、広帯域化された変調波に対しては時間シフト（波形のズラし）の方が正確。

### plot_results.py
- [MODIFY] CSVロード時のY軸補正ロジックに変わりなし (`df["level_db"] = df["level_db"] - df["sl_reference_db"]`)。
- [MODIFY] 必要に応じてグラフタイトルなどに周波数や条件等のメタデータを表示させる。

## Verification Plan
### Manual Verification
1. `python main.py` を実行し、初期ダイアログに周波数・変調タイプ・マスカーITDおよび**サウンドデバイスの選択フィールド**があることを確認。
2. 選択したサウンドデバイス（PC内蔵スピーカーや外部オーディオインターフェースなど）を切り替えて実行し、指定したデバイスから正しく音が再生されることを確認。（別のデバイスを指定した際にはそちらから音が出るか）
3. Phase 2 に移行後、回答(D or C)を5秒以上放置し、次の刺激が勝手に鳴らないことを確認。
4. CSVに出力されたデータに新しいパラメータ（`masker_itd_us` 等）が保存されていることを確認。
5. `phase2_stimulus.py` 内の検証用スクリプトで波形をプロットし、変調波とマスカーノイズの両方に指定されたITD（ズレ）が正しく反映されていることを目視またはスクリプトで確認。
