import pandas as pd

from app.market.service import MarketService


def test_service_exposes_provider_based_loader_method():
    class DummyLoader:
        def load_kline_data_with_provider(self, symbol, start_date=None, end_date=None, period="daily"):
            return pd.DataFrame([{"date": "2024-01-01", "close": 1.0}]), False

    service = MarketService(data_loader=DummyLoader())
    df, is_local = service.get_kline_data_with_provider("AAPL", start_date="2024-01-01")

    assert not is_local
    assert df.iloc[0]["close"] == 1.0
