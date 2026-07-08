# app/strategy/strategies/double_bottom.py
import pandas as pd
import numpy as np
from ..base import BaseStrategy


class DoubleBottomStrategy(BaseStrategy):
    """
    双底形态突破策略
    参数:
        lookback: 回看周期 (默认 30)
        tolerance: 价格容忍度 (%) (默认 3)
    """
    
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        lookback = self.params.get("lookback", 30)
        tolerance = self.params.get("tolerance", 3)
        
        df = df.copy()
        close = df["close"]
        low = df["low"]
        
        signals = pd.Series(0, index=df.index)
        
        for i in range(lookback, len(df)):
            window = df.iloc[i-lookback:i]
            current = df.iloc[i]
            
            # 找窗口内的两个低点
            lows = window["low"].values
            min_idx = np.argmin(lows)
            
            if min_idx < lookback // 2:
                # 前半段最低点
                first_low = lows[min_idx]
                # 后半段找第二个低点
                second_window = lows[min_idx + lookback//3:]
                if len(second_window) > 0:
                    second_low = np.min(second_window)
                    
                    # 两个低点接近（容忍度内）
                    diff = abs(first_low - second_low) / first_low * 100
                    if diff <= tolerance:
                        # 突破中间高点 → 买入
                        mid_high = window["high"].max()
                        if current["close"] > mid_high:
                            signals.iloc[i] = 1
        
        return signals