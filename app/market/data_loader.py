from datetime import datetime, timedelta

import pandas as pd


class MarketDataLoader:
    def __init__(self):
        self.sample_stocks = [
            {"symbol": "AAPL", "name": "苹果公司", "market": "NASDAQ"},
            {"symbol": "MSFT", "name": "微软", "market": "NASDAQ"},
            {"symbol": "TSLA", "name": "特斯拉", "market": "NASDAQ"},
            {"symbol": "BABA", "name": "阿里巴巴", "market": "NYSE"},
            {"symbol": "000001", "name": "平安银行", "market": "SZ"},
        ]

    def get_stock_list(self, limit: int = 20) -> list[dict]:
        return self.sample_stocks[:limit]

    def load_kline_data(self, symbol: str, start_date: str | None = None, end_date: str | None = None, period: str = "daily") -> pd.DataFrame:
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        # Fetch real data via AKShare. On any error, raise it so caller can return an error response.
        try:
            import akshare as ak  # type: ignore
        except Exception as e:
            raise ImportError("akshare is required for real data fetching: " + str(e))

        df_ak = None
        # Try several AKShare functions that might exist in different versions
        fetch_attempts = []
        try:
            if hasattr(ak, "stock_us_daily"):
                fetch_attempts.append(("stock_us_daily", ak.stock_us_daily))
            if hasattr(ak, "stock_zh_a_daily"):
                fetch_attempts.append(("stock_zh_a_daily", ak.stock_zh_a_daily))
            if hasattr(ak, "stock_zh_a_hist"):
                fetch_attempts.append(("stock_zh_a_hist", ak.stock_zh_a_hist))
        except Exception:
            # Some AKShare objects may behave oddly; ignore and proceed
            pass

        last_err = None
        for name, fn in fetch_attempts:
            try:
                # attempt common signature
                df_ak = fn(symbol=symbol, start_date=start_date, end_date=end_date)
                if df_ak is not None:
                    break
            except TypeError:
                # try alternative signature (symbol only)
                try:
                    df_ak = fn(symbol)
                    if df_ak is not None:
                        break
                except Exception as e:
                    last_err = e
            except Exception as e:
                last_err = e

        if df_ak is None:
            # No function succeeded
            if last_err:
                raise RuntimeError(f"AKShare fetch attempts failed: {last_err}")
            # no suitable AKShare fetch function available
            raise RuntimeError("No AKShare fetch function available for this environment")

        # If AKShare returned an empty DataFrame, return an empty normalized frame
        try:
            if getattr(df_ak, "empty", False):
                empty = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume", "symbol"])
                return empty

            df = df_ak.copy()
            # If date is index, reset it
            if not isinstance(df.index, pd.RangeIndex):
                df = df.reset_index()

            col_map = {}
            candidates = {
                "date": ["date", "日期", "trade_date", "timestamp", "time"],
                "open": ["open", "开盘", "开盘价"],
                "high": ["high", "最高"],
                "low": ["low", "最低"],
                "close": ["close", "收盘", "收盘价", "close_price"],
                "volume": ["volume", "成交量", "vol", "amount"],
            }

            for target, keys in candidates.items():
                for k in keys:
                    if k in df.columns:
                        col_map[target] = k
                        break

            for target in candidates:
                if target not in col_map:
                    for col in df.columns:
                        if col.lower() in [c.lower() for c in candidates[target]]:
                            col_map[target] = col
                            break

            normalized = pd.DataFrame()
            if "date" in col_map:
                normalized["date"] = pd.to_datetime(df[col_map["date"]])
            else:
                normalized["date"] = pd.to_datetime(df.iloc[:, 0])

            for key in ("open", "high", "low", "close", "volume"):
                if key in col_map:
                    normalized[key] = pd.to_numeric(df[col_map[key]], errors="coerce")
                else:
                    normalized[key] = pd.NA

            normalized["symbol"] = symbol
            if "close" in normalized.columns:
                normalized = normalized.dropna(subset=["close"]) if not normalized.empty else normalized

            normalized = normalized.sort_values("date")
            normalized = normalized.reset_index(drop=True)
            return normalized
        except Exception as e:
            # Parsing error should be surfaced to caller
            raise RuntimeError("Failed to parse AKShare data: " + str(e))
