# app/strategy/strategies/vwap.py
import pandas as pd
import numpy as np
from ..base import BaseStrategy

class VWAPStrategy(BaseStrategy):
    """
    VWAP 突破策略
    价格高于 VWAP 买入，低于 VWAP 卖出
    """
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        period = self.params.get("period", 20)
        df = df.copy()
        # 计算 VWAP
        df["vp"] = df["volume"] * df["close"]
        df["cum_vp"] = df["vp"].rolling(period).sum()
        df["cum_vol"] = df["volume"].rolling(period).sum()
        df["vwap"] = df["cum_vp"] / df["cum_vol"]
        
        signals = pd.Series(0, index=df.index)
        signals[df["close"] > df["vwap"]] = 1
        signals[df["close"] < df["vwap"]] = -1
        return signals