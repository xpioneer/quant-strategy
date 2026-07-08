# app/strategy/strategies/turtle.py
import pandas as pd
import numpy as np
from ..base import BaseStrategy


class TurtleStrategy(BaseStrategy):
    """
    海龟交易法则（唐奇安通道突破）
    参数:
        entry_period: 入场通道周期 (默认 20)
        exit_period: 出场通道周期 (默认 10)
    """
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        entry = self.params.get("entry_period", 20)
        exit_p = self.params.get("exit_period", 10)
        
        df = df.copy()
        
        # 唐奇安通道
        df["entry_high"] = df["high"].rolling(window=entry).max()
        df["entry_low"] = df["low"].rolling(window=entry).min()
        df["exit_high"] = df["high"].rolling(window=exit_p).max()
        df["exit_low"] = df["low"].rolling(window=exit_p).min()
        
        signals = pd.Series(0, index=df.index)
        
        # 突破20日高点 → 买入
        buy_mask = (df["close"] > df["entry_high"].shift(1))
        signals[buy_mask] = 1
        
        # 跌破10日低点 → 卖出
        sell_mask = (df["close"] < df["exit_low"].shift(1))
        signals[sell_mask] = -1
        
        return signals