class BaseStrategy:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description


class MACrossStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(name="MA Cross", description="均线交叉策略")


class MACDStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(name="MACD", description="MACD 策略")


class TurtleStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(name="Turtle", description="海龟交易策略")
