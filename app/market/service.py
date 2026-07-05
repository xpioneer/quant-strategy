from app.market.data_loader import MarketDataLoader


class MarketService:
    def __init__(self, data_loader: MarketDataLoader | None = None):
        self.data_loader = data_loader or MarketDataLoader()

    def get_stock_list(self, limit: int = 20) -> list[dict]:
        return self.data_loader.get_stock_list(limit=limit)

    def get_kline_data(self, symbol: str, start_date: str | None = None, end_date: str | None = None, period: str = "daily"):
        return self.data_loader.load_kline_data(symbol=symbol, start_date=start_date, end_date=end_date, period=period)
