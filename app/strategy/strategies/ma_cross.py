# app/strategy/strategies/ma_cross.py
import pandas as pd
import numpy as np
from ..base import BaseStrategy

class MACrossStrategy(BaseStrategy):
    """
    均线金叉死叉策略
    参数:
        fast_period: 短期均线周期 (默认 5)
        slow_period: 长期均线周期 (默认 20)
    """
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        fast = self.params.get("fast_period", 5)
        slow = self.params.get("slow_period", 20)
        
        # 计算均线
        df = df.copy()
        df["ma_fast"] = df["close"].rolling(window=fast).mean()
        df["ma_slow"] = df["close"].rolling(window=slow).mean()
        
        # 生成信号
        signals = pd.Series(0, index=df.index)
        
        # 金叉: fast 上穿 slow → 买入
        buy_mask = (df["ma_fast"] > df["ma_slow"]) & (df["ma_fast"].shift(1) <= df["ma_slow"].shift(1))
        signals[buy_mask] = 1
        
        # 死叉: fast 下穿 slow → 卖出
        sell_mask = (df["ma_fast"] < df["ma_slow"]) & (df["ma_fast"].shift(1) >= df["ma_slow"].shift(1))
        signals[sell_mask] = -1
        
        return signals