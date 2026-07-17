import backtrader as bt

class MACDDivergence(bt.Strategy):
    """
    修复版 MACD 底背离策略
    """
    params = (
        ('lookback', 90),        # 回溯周期
        ('stop_loss_pct', 0.07), # 止损 7%
        ('take_profit_pct', 0.2),# 止盈 20%
        ('min_hist_diff', 0.01), # MACD 柱差值阈值（过滤噪音）
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(self.data.close)
        self.macd_hist = self.macd.macd - self.macd.signal
        self.entry_price = None

    def next(self):
        if len(self) < self.params.lookback:
            return

        # 获取回溯周期内的数据
        closes = self.data.close.get(size=self.params.lookback)
        hists = self.macd_hist.get(size=self.params.lookback)

        # 当前值
        current_close = self.data.close[0]
        current_hist = self.macd_hist[0]

        if not self.position:
            # ----- 开仓条件（放宽版）-----
            
            # 1. 价格接近 N 日低点（不要求创新低）
            recent_low = min(closes)
            near_low = current_close <= recent_low * 1.02  # 在最低点 2% 范围内
            
            # 2. MACD 柱在零轴下方且开始回升
            past_hists = hists[:-1]
            lowest_hist = min(past_hists)
            
            # 当前 MACD 柱比最低点时高了，且差值超过阈值
            hist_recovery = (current_hist - lowest_hist) > self.params.min_hist_diff
            
            # 3. MACD 柱本身还在零轴下方（底背离特征）
            below_zero = current_hist < 0
            
            if near_low and hist_recovery and below_zero:
                self.buy()
                self.entry_price = current_close
                print(f"[{self.data.datetime.date(0)}] 买入: 价格 {current_close:.2f}, "
                      f"MACD柱 {current_hist:.4f}")

        else:
            # ----- 平仓条件 -----
            if self.entry_price is None:
                return
                
            ret = (current_close - self.entry_price) / self.entry_price
            
            # 止损
            if ret < -self.params.stop_loss_pct:
                self.close()
                self.entry_price = None
                print(f"[{self.data.datetime.date(0)}] 止损: 价格 {current_close:.2f}, "
                      f"盈亏 {ret*100:.2f}%")
            
            # 止盈
            elif ret > self.params.take_profit_pct:
                self.close()
                self.entry_price = None
                print(f"[{self.data.datetime.date(0)}] 止盈: 价格 {current_close:.2f}, "
                      f"盈亏 {ret*100:.2f}%")
            
            # 如果 MACD 柱跌破买入时水平，提前止损
            elif current_hist < hists[-2] * 0.5:
                self.close()
                self.entry_price = None
                print(f"[{self.data.datetime.date(0)}] MACD恶化止损: 价格 {current_close:.2f}")