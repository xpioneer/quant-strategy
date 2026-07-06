# app/strategy/strategies/rsi.py
import pandas as pd
import numpy as np
from ..base import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    RSI 超买超卖策略
    参数:
        period: RSI 计算周期 (默认 14)
        oversold: 超卖线 (默认 30)
        overbought: 超买线 (默认 70)
    """

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        period = self.params.get("period", 14)
        oversold = self.params.get("oversold", 30)
        overbought = self.params.get("overbought", 70)

        df = df.copy()
        close = df["close"]

        # 计算 RSI
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(window=period).mean()
        loss = (-delta.clip(upper=0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        signals = pd.Series(0, index=df.index)

        # 上穿超卖 → 买入
        buy_mask = (rsi < oversold) & (rsi.shift(1) >= oversold)
        signals[buy_mask] = 1

        # 下穿超买 → 卖出
        sell_mask = (rsi > overbought) & (rsi.shift(1) <= overbought)
        signals[sell_mask] = -1

        return signals