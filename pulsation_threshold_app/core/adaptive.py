import numpy as np

class AdaptiveStaircase:
    """
    Interleaved adaptive procedure (Plack & Oxenham, 2000) for Pulsation Threshold
    
    信号レベル(Signal Level)を変化させる場合のロジック
    - Continuous (連続): ターゲットより信号が弱い → レベルを上げる (UP)
    - Pulsed (脈動): ターゲットより信号が強い → レベルを下げる (DOWN)
    """
    def __init__(self, target_percent, start_level=60.0):
        self.target_percent = target_percent 
        self.current_level = start_level
        self.step_size = 5.0  # 初期ステップ 5dB
        
        self.history = []     # (level, response)
        self.reversals = []   # level at reversal points
        self.direction = 0    # 1: Up, -1: Down
        self.consecutive_continuous = 0
        self.consecutive_pulsed = 0
        self.finished = False

    def get_current_level(self):
        return self.current_level

    def update(self, response_is_continuous):
        """
        回答を受け取り、次のレベルを決定する。
        """
        self.history.append((self.current_level, response_is_continuous))
        
        prev_level = self.current_level
        
        # --- ロジック分岐 ---
        # Track 1 (Target 70.7% Continuous) -> 2 Continuous で UP (Signal Increase)
        if self.target_percent > 50: 
            if response_is_continuous:
                self.consecutive_continuous += 1
                self.consecutive_pulsed = 0
            else:
                self.consecutive_pulsed += 1
                self.consecutive_continuous = 0
                
            if self.consecutive_continuous >= 2:
                self.current_level += self.step_size # Signal UP
                self.consecutive_continuous = 0
                new_direction = 1
            elif not response_is_continuous: # 1 Pulsed
                self.current_level -= self.step_size # Signal DOWN
                new_direction = -1
            else:
                new_direction = self.direction 

        # Track 2 (Target 29.3% Continuous) -> 2 Pulsed で DOWN (Signal Decrease)
        else: 
            if response_is_continuous:
                self.consecutive_continuous += 1
                self.consecutive_pulsed = 0
            else:
                self.consecutive_pulsed += 1
                self.consecutive_continuous = 0

            if self.consecutive_pulsed >= 2:
                self.current_level -= self.step_size # Signal DOWN
                self.consecutive_pulsed = 0
                new_direction = -1
            elif response_is_continuous: # 1 Continuous
                self.current_level += self.step_size # Signal UP
                new_direction = 1
            else:
                new_direction = self.direction

        # --- 反転判定と終了判定 ---
        if self.direction != 0 and new_direction != 0 and self.direction != new_direction:
            self.reversals.append(prev_level)
            # 3回反転でステップサイズ変更
            if len(self.reversals) == 3:
                self.step_size = 2.0
            # 7回反転で終了
            if len(self.reversals) >= 7:
                self.finished = True
        
        self.direction = new_direction

    def get_threshold(self):
        """最後の4回の反転の平均を計算"""
        if len(self.reversals) >= 4:
            return np.mean(self.reversals[-4:])
        return None


class ThreeDownOneUpStaircase:
    """
    可聴閾値測定用の 3-down 1-up 適応法 (Levitt, 1971)
    正答率 79.4% に収束する。
    
    ロジック:
    - 3回連続正解 (Correct) -> レベルを下げる (Harder)
    - 1回不正解 (Incorrect) -> レベルを上げる (Easier)
    """
    def __init__(self, start_level, initial_step=4.0, min_step=2.0):
        self.current_level = start_level
        self.step_size = initial_step
        self.min_step = min_step
        
        self.consecutive_correct = 0
        self.reversals = []
        self.direction = 0 # 1: Up (Level Increase), -1: Down (Level Decrease)
        self.finished = False
        self.history = []

    def get_current_level(self):
        return self.current_level

    def update(self, is_correct):
        """
        is_correct: True (正解) / False (不正解)
        """
        self.history.append((self.current_level, is_correct))
        prev_level = self.current_level
        new_direction = self.direction

        if is_correct:
            self.consecutive_correct += 1
            if self.consecutive_correct >= 3:
                self.current_level -= self.step_size # 3連勝でレベルを下げる（音を小さく）
                self.consecutive_correct = 0
                new_direction = -1
        else:
            self.consecutive_correct = 0 # リセット
            self.current_level += self.step_size # 1回ミスでレベルを上げる（音を大きく）
            new_direction = 1

        # 反転判定
        if self.direction != 0 and new_direction != 0 and self.direction != new_direction:
            self.reversals.append(prev_level)
            # 反転のたびにステップサイズを小さくする（最小値まで）
            if self.step_size > self.min_step:
                self.step_size /= 2.0
                if self.step_size < self.min_step:
                    self.step_size = self.min_step
            
            # 6回反転したら終了（一般的には6-8回）
            if len(self.reversals) >= 6:
                self.finished = True
        
        self.direction = new_direction

    def get_threshold(self):
        """最後の偶数回の反転の平均を閾値とする"""
        if len(self.reversals) >= 4:
            return np.mean(self.reversals[-4:])
        return self.current_level