# app/strategy/strategies/macd.py
import pandas as pd
import numpy as np
from ..base import BaseStrategy


class MACDStrategy(BaseStrategy):
    """
    MACD 金叉死叉策略
    参数:
        fast: 快线周期 (默认 12)
        slow: 慢线周期 (默认 26)
        signal: 信号线周期 (默认 9)
    """
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        fast = self.params.get("fast", 12)
        slow = self.params.get("slow", 26)
        signal = self.params.get("signal", 9)
        
        df = df.copy()
        close = df["close"]
        
        # 计算 MACD
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        df["dif"] = ema_fast - ema_slow
        df["dea"] = df["dif"].ewm(span=signal, adjust=False).mean()
        df["macd"] = 2 * (df["dif"] - df["dea"])
        
        signals = pd.Series(0, index=df.index)
        
        # DIF 上穿 DEA → 买入
        buy_mask = (df["dif"] > df["dea"]) & (df["dif"].shift(1) <= df["dea"].shift(1))
        signals[buy_mask] = 1
        
        # DIF 下穿 DEA → 卖出
        sell_mask = (df["dif"] < df["dea"]) & (df["dif"].shift(1) >= df["dea"].shift(1))
        signals[sell_mask] = -1
        
        return signals