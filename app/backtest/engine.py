from app.market.service import MarketService


class BacktestEngine:
    def __init__(self, market_service: MarketService | None = None):
        self.market_service = market_service or MarketService()

    def run(self, strategy_name: str, symbol: str, start_date: str | None = None, end_date: str | None = None):
        df = self.market_service.get_kline_data(symbol=symbol, start_date=start_date, end_date=end_date)
        if df.empty:
            return {"strategy": strategy_name, "symbol": symbol, "result": "no_data"}

        close = df["close"].astype(float)
        short_ma = close.rolling(window=5).mean()
        long_ma = close.rolling(window=20).mean()
        signals = (short_ma > long_ma).astype(int)
        signal_changes = signals.diff().fillna(0)
        trade_count = int(signal_changes.abs().sum())
        return_rate = float((close.iloc[-1] / close.iloc[0]) - 1) if len(close) > 1 else 0.0

        return {
            "strategy": strategy_name,
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "trade_count": trade_count,
            "return_rate": round(return_rate, 4),
            "final_value": round(10000 * (1 + return_rate), 2),
        }

    def compare(self, strategies: list[str], symbol: str, start_date: str | None = None, end_date: str | None = None):
        return [self.run(strategy_name=strategy, symbol=symbol, start_date=start_date, end_date=end_date) for strategy in strategies]
