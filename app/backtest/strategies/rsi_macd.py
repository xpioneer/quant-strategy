import backtrader as bt

class RSI_MACD_Divergence(bt.Strategy):
    """
    RSI + MACD 双重确认底背离
    """
    params = (
        ('lookback', 60),
        ('rsi_period', 14),
        ('rsi_oversold', 35),    # RSI 超卖阈值（放宽到 35）
        ('stop_loss_pct', 0.06),
        ('take_profit_pct', 0.15),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(self.data.close)
        self.macd_hist = self.macd.macd - self.macd.signal
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.entry_price = None

    def next(self):
        if len(self) < self.params.lookback:
            return

        current_close = self.data.close[0]
        current_hist = self.macd_hist[0]
        current_rsi = self.rsi[0]

        if not self.position:
            # 获取过去 N 天的数据
            closes = self.data.close.get(size=self.params.lookback)
            hists = self.macd_hist.get(size=self.params.lookback)
            rsis = self.rsi.get(size=self.params.lookback)

            # 价格在低位
            price_position = (current_close - min(closes)) / (max(closes) - min(closes))
            at_low = price_position < 0.3  # 在最近高低点区间的下 30%

            # MACD 柱从最低点回升
            min_hist = min(hists)
            hist_up = current_hist > min_hist * 0.8  # 回升到最低点的 80% 以上

            # RSI 在超卖区或刚从超卖区出来
            rsi_ok = current_rsi < self.params.rsi_oversold or \
                     (current_rsi < 45 and rsis[-2] < self.params.rsi_oversold)

            if at_low and hist_up and rsi_ok:
                self.buy()
                self.entry_price = current_close
                print(f"[{self.data.datetime.date(0)}] 买入: 价格 {current_close:.2f}, "
                      f"RSI {current_rsi:.1f}, MACD柱 {current_hist:.4f}")

        else:
            if self.entry_price is None:
                return

            ret = (current_close - self.entry_price) / self.entry_price

            if ret < -self.params.stop_loss_pct:
                self.close()
                self.entry_price = None
            elif ret > self.params.take_profit_pct:
                self.close()
                self.entry_price = None