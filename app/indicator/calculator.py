import pandas as pd
from typing import List


class IndicatorCalculator:
    def __init__(self):
        pass

    def calculate_ma(self, df: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
        result = df.copy()
        for period in periods:
            result[f'MA{period}'] = df['close'].rolling(window=period).mean()
        return result

    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> pd.DataFrame:
        result = df.copy()
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        result['MACD'] = ema_fast - ema_slow
        result['MACD_Signal'] = result['MACD'].ewm(span=signal, adjust=False).mean()
        result['MACD_Hist'] = result['MACD'] - result['MACD_Signal']
        return result

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        result = df.copy()
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        result['RSI'] = 100 - (100 / (1 + rs))
        return result

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.calculate_ma(df)
        df = self.calculate_macd(df)
        df = self.calculate_rsi(df)
        return df
