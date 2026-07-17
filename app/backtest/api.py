from fastapi import APIRouter, Body
import pandas as pd

from app.backtest.engine import BacktestEngine
from app.common.schemas import Response
from app.market.service import MarketService
from .bt_engine import BacktraderEngine
from .strategies.golden_cross import GoldenCross
from .strategies.turtle_trade import TurtleTrade
from .strategies.macd_divergence import MACDDivergence
from .strategies.rsi_macd import RSI_MACD_Divergence

router = APIRouter()
engine = BacktestEngine()

bt_engine = BacktraderEngine()
# 所有策略
strategies = [
    ('双均线金叉', GoldenCross, {'short': 10, 'long': 30}),
    ('海龟交易', TurtleTrade, {'period': 20}),
    ('MACD底背离', MACDDivergence, {}),
    ('RSI_MACD底背离', RSI_MACD_Divergence, {'lookback': 60}),
]


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

@router.post("/bt")
def bt_backtest(
    symbol: str = Body(...),
    start_date: str = Body(None),
    end_date: str = Body(None),
):
    market_service = MarketService()
    df, _ = market_service.get_kline_data_with_provider(symbol=symbol, start_date=start_date, end_date=end_date)
    # 必须显式确保：
    # df['date'] = pd.to_datetime(df['date']) # 转为 datetime
    # df = df.sort_values('date')             # 确保升序
    # df = df.set_index('date')               # 设置为索引
    results = []
    for name, strategy_class, params in strategies:
        print(f'\n========== {name} ==========')
        result = bt_engine.run_strategy(df, strategy_class, **params)
        result['strategy_name'] = name
        results.append(result)
    return Response(data=results)
