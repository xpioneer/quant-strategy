from datetime import datetime

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
    df, local = market_service.get_kline_data(symbol=symbol, start_date=start_date, end_date=end_date, period=period)
    return Response(data={
        "symbol": symbol,
        "period": period,
        "local": local,
        "rows": df.to_dict(orient="records"),
    })


@router.get("/stock/{symbol}")
def get_kline(symbol: str, start_date: str | None = None, end_date: str | None = None, period: str = "daily"):
    df, local = market_service.get_kline_data_with_provider(symbol=symbol, start_date=start_date, end_date=end_date, period=period)
    return Response(data={
        "symbol": symbol,
        "period": period,
        "local": local,
        "rows": df.to_dict(orient="records"),
    })


@router.delete("/stock/{symbol}")
def delete_stock(symbol: str):
    msg = market_service.delete_symbol(symbol=symbol)
    return Response(data={
        "symbol": symbol,
        "time": datetime.now(),
        "msg": msg,
    })