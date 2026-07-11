import yfinance as yf
import pandas as pd
from app.market.providers.base import BaseDataProvider

class YahooProvider(BaseDataProvider):
    def fetch_history(self, symbol: str, period: str = 'daily') -> pd.DataFrame:
        is_a_share = symbol.isdigit() and len(symbol) == 6
        if is_a_share:
            suffix = ".SZ" if symbol.startswith(("0", "3")) else ".SS"
            yf_symbol = f"{symbol}{suffix}"
        else:
            yf_symbol = symbol.upper()
        
        print(f"[INFO] 尝试 yfinance 获取 {yf_symbol} ...")
        ticker = yf.Ticker(yf_symbol)
        df_yf = ticker.history(period="max", auto_adjust=True)

        # df_yf = yf.download(
        #     yf_symbol,
        #     start="2020-01-01",
        #     end="2025-01-01",
        #     auto_adjust=True
        # )
        
        if df_yf.empty:
            print(f"[WARN] yfinance 未获取到 {yf_symbol} 的数据")
            return pd.DataFrame()
        
        df = df_yf.copy()
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        
        normalized["date"] = pd.to_datetime(df["date"])
        normalized["open"] = pd.to_numeric(df["open"], errors="coerce")
        normalized["high"] = pd.to_numeric(df["high"], errors="coerce")
        normalized["low"] = pd.to_numeric(df["low"], errors="coerce")
        normalized["close"] = pd.to_numeric(df["close"], errors="coerce")
        normalized["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        
        # Yahoo 无成交额，用 volume * close 近似
        normalized["amount"] = normalized["volume"] * normalized["close"]
        
        # 自行计算涨跌幅
        normalized["pct_change"] = normalized["close"].pct_change() * 100
        normalized["change"] = normalized["close"].diff()
        normalized["amplitude"] = (normalized["high"] - normalized["low"]) / normalized["close"].shift(1) * 100
        normalized["turnover_rate"] = pd.NA
        normalized["symbol"] = symbol
        
        normalized = normalized.dropna(subset=["close"])
        normalized = normalized.sort_values("date").reset_index(drop=True)
        
        return normalized
