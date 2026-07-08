# app/strategy/strategies/bollinger.py
import pandas as pd
import numpy as np
from ..base import BaseStrategy


class BollingerStrategy(BaseStrategy):
    """
    布林带均值回归策略
    参数:
        period: 中轨周期 (默认 20)
        std_dev: 标准差倍数 (默认 2)
    """
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        period = self.params.get("period", 20)
        std_dev = self.params.get("std_dev", 2)
        
        df = df.copy()
        close = df["close"]
        
        # 计算布林带
        df["mid"] = close.rolling(window=period).mean()
        df["std"] = close.rolling(window=period).std()
        df["upper"] = df["mid"] + std_dev * df["std"]
        df["lower"] = df["mid"] - std_dev * df["std"]
        
        signals = pd.Series(0, index=df.index)
        
        # 价格触及下轨 → 买入（超卖反弹）
        buy_mask = (close <= df["lower"]) & (close.shift(1) > df["lower"].shift(1))
        signals[buy_mask] = 1
        
        # 价格触及上轨 → 卖出（超买回落）
        sell_mask = (close >= df["upper"]) & (close.shift(1) < df["upper"].shift(1))
        signals[sell_mask] = -1
        
        return signals