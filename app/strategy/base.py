# app/strategy/base.py
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, Any

class BaseStrategy(ABC):
    """策略基类"""
    
    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}
        self.signals = None  # 信号序列: 1=买入, -1=卖出, 0=持有
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        生成交易信号
        返回 pd.Series, 值: 1=买入, -1=卖出, 0=持有
        """
        pass
    
    def get_params(self) -> Dict[str, Any]:
        return self.params