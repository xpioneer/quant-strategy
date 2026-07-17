import backtrader as bt

class GoldenCross(bt.Strategy):
    params = (('short', 10), ('long', 30))

    def __init__(self):
        self.short_ma = bt.indicators.SMA(self.data.close, period=self.params.short)
        self.long_ma = bt.indicators.SMA(self.data.close, period=self.params.long)
        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()