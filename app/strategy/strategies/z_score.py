# app/strategy/strategies/z_score.py
import pandas as pd
import numpy as np
from ..base import BaseStrategy


class ZScoreStrategy(BaseStrategy):
    """
    Z-Score 均值回归策略
    价格偏离均值 2 个标准差时反向操作
    """
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        period = self.params.get("period", 20)
        z_threshold = self.params.get("z_threshold", 2)
        
        df = df.copy()
        df["ma"] = df["close"].rolling(period).mean()
        df["std"] = df["close"].rolling(period).std()
        df["z_score"] = (df["close"] - df["ma"]) / df["std"]
        
        signals = pd.Series(0, index=df.index)
        signals[df["z_score"] < -z_threshold] = 1   # 超卖买入
        signals[df["z_score"] > z_threshold] = -1   # 超买卖出
        return signals