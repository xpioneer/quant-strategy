import backtrader as bt

class TurtleTrade(bt.Strategy):
    params = (('period', 20), )

    def __init__(self):
        self.highest = bt.indicators.Highest(self.data.high, period=self.params.period)
        self.lowest = bt.indicators.Lowest(self.data.low, period=self.params.period)

    def next(self):
        if not self.position:
            if self.data.close[0] > self.highest[-1]:
                self.buy()
        else:
            if self.data.close[0] < self.lowest[-1]:
                self.close()