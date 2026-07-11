from __future__ import annotations

import pandas as pd

from app.database import SessionLocal
from app.database.models import Kline
from app.market.providers.akshare_provider import AkShareProvider
from app.market.providers.base import BaseDataProvider
from app.market.providers.yahoo_provider import YahooProvider


class ProviderMarketDataLoader:
    def __init__(self, providers: list[BaseDataProvider] | None = None):
        self.providers = providers or [YahooProvider(), AkShareProvider()]
        self.sample_stocks = [
            {"symbol": "AAPL", "name": "苹果公司", "market": "NASDAQ"},
            {"symbol": "MSFT", "name": "微软", "market": "NASDAQ"},
            {"symbol": "TSLA", "name": "特斯拉", "market": "NASDAQ"},
            {"symbol": "BABA", "name": "阿里巴巴", "market": "NYSE"},
            {"symbol": "000001", "name": "平安银行", "market": "SZ"},
        ]

    def get_stock_list(self, limit: int = 20) -> list[dict]:
        return self.sample_stocks[:limit]

    def get_stock_data(self, symbol: str) -> dict | None:
        for stock in self.sample_stocks:
            if stock["symbol"] == symbol:
                return stock
        return None

    def load_kline_data_with_provider(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        period: str = "daily",
    ) -> tuple[pd.DataFrame, bool]:
        start_dt = pd.to_datetime(start_date) if start_date else None
        end_dt = pd.to_datetime(end_date) if end_date else None
        # 先从本地数据库查询
        session = SessionLocal()
        try:
            query = session.query(Kline).filter(Kline.symbol == symbol)
            has_symbol = query.first()
            if has_symbol:
                if start_dt is not None:
                    query = query.filter(Kline.date >= start_dt)
                if end_dt is not None:
                    query = query.filter(Kline.date <= end_dt)

                db_rows = query.order_by(Kline.date).all()
                if db_rows:
                    data = [
                        {
                            "date": r.date,
                            "symbol": r.symbol,
                            "open": r.open,
                            "high": r.high,
                            "low": r.low,
                            "close": r.close,
                            "volume": r.volume,
                            "amount": r.amount,
                            "amplitude": r.amplitude,
                            "pct_change": r.pct_change,
                            "change": r.change,
                            "turnover_rate": r.turnover_rate,
                        }
                        for r in db_rows
                    ]
                    return pd.DataFrame(data), True

            # 这里去远程获取，使用不同的provider尝试获取数据
            for provider in self.providers:
                try:
                    df_remote = provider.fetch_history(symbol=symbol, period=period)
                except Exception as exc:
                    print(f"[WARN] provider {provider.__class__.__name__} failed: {exc}")
                    continue

                if df_remote is None or getattr(df_remote, "empty", True):
                    continue

                normalized = self._normalize_provider_dataframe(df_remote, symbol)
                if normalized.empty:
                    continue

                self._save_to_db(session, symbol, normalized)

                result_df = normalized.copy()
                if start_dt is not None:
                    result_df = result_df[result_df["date"] >= start_dt]
                if end_dt is not None:
                    result_df = result_df[result_df["date"] <= end_dt]
                return result_df.reset_index(drop=True), False

            empty = pd.DataFrame(
                columns=[
                    "date",
                    "symbol",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "amount",
                    "amplitude",
                    "pct_change",
                    "change",
                    "turnover_rate",
                ]
            )
            return empty, False
        finally:
            session.close()

    def load_kline_data(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
        period: str = "daily",
    ) -> tuple[pd.DataFrame, bool]:
        return self.load_kline_data_with_provider(symbol=symbol, start_date=start_date, end_date=end_date, period=period)

    def delete_symbol(self, symbol: str, period: str = "daily") -> str:
        session = SessionLocal()
        try:
            session.query(Kline).filter(Kline.symbol == symbol).delete(synchronize_session=False)
            session.commit()
        except Exception as exc:
            session.rollback()
            raise RuntimeError("Failed to delete existing Kline rows: " + str(exc))
        finally:
            session.close()
        return "delete done"

    def _normalize_provider_dataframe(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        if df is None or getattr(df, "empty", True):
            return pd.DataFrame()

        normalized = pd.DataFrame()
        if "date" in df.columns:
            normalized["date"] = pd.to_datetime(df["date"], errors="coerce")
        else:
            normalized["date"] = pd.to_datetime(df.iloc[:, 0], errors="coerce")

        for col in ["open", "high", "low", "close", "volume", "amount", "amplitude", "pct_change", "change", "turnover_rate"]:
            if col in df.columns:
                normalized[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                normalized[col] = pd.NA

        normalized["symbol"] = symbol
        normalized = normalized.dropna(subset=["close"]).sort_values("date").reset_index(drop=True)

        if "amount" not in normalized.columns:
            normalized["amount"] = pd.NA
        if normalized["amount"].isna().all() and "volume" in normalized.columns and "close" in normalized.columns:
            normalized["amount"] = normalized["volume"] * normalized["close"]

        return normalized

    def _save_to_db(self, session, symbol: str, df: pd.DataFrame) -> None:
        if df.empty:
            return

        try:
            session.query(Kline).filter(Kline.symbol == symbol).delete(synchronize_session=False)
            rows = []
            for _, row in df.iterrows():
                dt = pd.to_datetime(row["date"]).to_pydatetime()
                rows.append(
                    Kline(
                        symbol=symbol,
                        date=dt,
                        open=float(row.get("open") if pd.notna(row.get("open")) else 0.0),
                        high=float(row.get("high") if pd.notna(row.get("high")) else 0.0),
                        low=float(row.get("low") if pd.notna(row.get("low")) else 0.0),
                        close=float(row.get("close") if pd.notna(row.get("close")) else 0.0),
                        volume=float(row.get("volume") if pd.notna(row.get("volume")) else 0.0),
                        amount=float(row.get("amount") if pd.notna(row.get("amount")) else 0.0),
                        amplitude=float(row.get("amplitude") if pd.notna(row.get("amplitude")) else 0.0),
                        pct_change=float(row.get("pct_change") if pd.notna(row.get("pct_change")) else 0.0),
                        change=float(row.get("change") if pd.notna(row.get("change")) else 0.0),
                        turnover_rate=float(row.get("turnover_rate") if pd.notna(row.get("turnover_rate")) else 0.0),
                    )
                )
            if rows:
                session.add_all(rows)
            session.commit()
        except Exception as exc:
            session.rollback()
            raise RuntimeError("Failed to save provider data to DB: " + str(exc))
