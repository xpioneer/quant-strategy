from fastapi import APIRouter

from app.common.schemas import Response
from app.market.service import MarketService

router = APIRouter()
market_service = MarketService()


@router.get("/stocks")
def get_stocks(limit: int = 20):
    stocks = market_service.get_stock_list(limit=limit)
    return Response(data=stocks)


@router.get("/kline/{symbol}")
def get_kline(symbol: str, start_date: str | None = None, end_date: str | None = None, period: str = "daily"):
    df = market_service.get_kline_data(symbol=symbol, start_date=start_date, end_date=end_date, period=period)
    return Response(data={
        "symbol": symbol,
        "period": period,
        "rows": df.to_dict(orient="records"),
    })
