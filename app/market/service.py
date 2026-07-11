from typing import Any

from app.market.providers.loader import ProviderMarketDataLoader


class MarketService:
    def __init__(self, data_loader: Any = None):
        self.data_loader = data_loader or ProviderMarketDataLoader()

    def get_stock_list(self, limit: int = 20) -> list[dict]:
        return self.data_loader.get_stock_list(limit=limit)

    def get_kline_data(self, symbol: str, start_date: str | None = None, end_date: str | None = None, period: str = "daily"):
        return self.data_loader.load_kline_data(symbol=symbol, start_date=start_date, end_date=end_date, period=period)

    def get_kline_data_with_provider(self, symbol: str, start_date: str | None = None, end_date: str | None = None, period: str = "daily"):
        return self.data_loader.load_kline_data_with_provider(symbol=symbol, start_date=start_date, end_date=end_date, period=period)

    def delete_symbol(self, symbol: str, period: str = "daily"):
        return self.data_loader.delete_symbol(symbol=symbol, period=period)