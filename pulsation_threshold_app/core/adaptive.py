class AdaptiveStaircase:
    """論文の interleaved adaptive procedure 管理 [cite: 85, 96]"""
    def __init__(self, target_percent):
        self.target_percent = target_percent  # 70.7% または 29.3% [cite: 96]
        self.levels = []
        self.reversals = []
        self.current_step_size = 5  # 初期ステップ 5dB [cite: 101]
        self.finished = False

    def update(self, response_is_continuous):
        """
        回答を受け取り、次のレベルを決定。
        3回の反転後にステップサイズを2dBに変更 [cite: 102]。
        7回の反転で終了 [cite: 103]。
        """
        pass

    def get_threshold(self):
        """最後の4回の反転の平均を計算 [cite: 103]"""
        pass