from fastapi import APIRouter

from app.backtest.engine import BacktestEngine
from app.common.schemas import Response

router = APIRouter()
engine = BacktestEngine()


@router.post("/run")
def run_backtest(payload: dict):
    strategy_name = payload.get("strategy", "MA Cross")
    symbol = payload.get("symbol", "AAPL")
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")
    result = engine.run(strategy_name=strategy_name, symbol=symbol, start_date=start_date, end_date=end_date)
    return Response(data=result)


@router.post("/compare")
def compare_backtest(payload: dict):
    strategies = payload.get("strategies", ["MA Cross", "MACD"])
    symbol = payload.get("symbol", "AAPL")
    start_date = payload.get("start_date")
    end_date = payload.get("end_date")
    result = engine.compare(strategies=strategies, symbol=symbol, start_date=start_date, end_date=end_date)
    return Response(data=result)
