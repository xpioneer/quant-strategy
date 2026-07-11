from abc import ABC, abstractmethod
import pandas as pd

class BaseDataProvider(ABC):
    @abstractmethod
    def fetch_history(self, symbol: str, period: str = 'daily') -> pd.DataFrame:
        """返回标准化后的 DataFrame (date, symbol, open, high, low, close, volume, amount, amplitude, pct_change, change, turnover_rate)"""
        pass
