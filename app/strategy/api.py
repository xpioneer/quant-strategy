from fastapi import APIRouter, Query, Body
from loguru import logger
from app.common.schemas import Response
from ..strategy.backtest import BacktestEngine
from ..strategy.strategies.ma_cross import MACrossStrategy
from ..strategy.strategies.rsi import RSIStrategy
from ..market.service import MarketService

router = APIRouter()


@router.get("/strategies", response_model=Response[list])
def get_strategies():
    logger.info("获取策略列表")
    return Response(data=[])


@router.get("/available-strategies", response_model=Response[list])
def get_available_strategies():
    logger.info("获取可用策略列表")
    strategies = [
        {
            'name': 'MA Cross',
            'description': '均线交叉策略',
            'type': 'ma_cross',
            'parameters': {
                'fast_period': 5,
                'slow_period': 20
            }
        },
        {
            'name': 'MACD',
            'description': 'MACD策略',
            'type': 'macd',
            'parameters': {
                'fast': 12,
                'slow': 26,
                'signal': 9
            }
        },
        {
            'name': 'Turtle',
            'description': '海龟交易策略',
            'type': 'turtle',
            'parameters': {
                'entry_period': 20,
                'exit_period': 10
            }
        }
    ]
    return Response(data=strategies)

@router.post("/backtest")
def run_backtest(
    symbol: str = Body(..., description="股票代码"),
    strategy_type: str = Body("ma_cross", description="策略类型: ma_cross / rsi"),
    fast_period: int = Body(5, ge=2, le=100),
    slow_period: int = Body(20, ge=5, le=200),
    start_date: str = Body(None),
    end_date: str = Body(None),
    initial_capital: float = Body(100000.0, ge=1000)
):
    """运行策略回测"""
    # 获取 K 线数据
    market_service = MarketService()
    df, is_local = market_service.get_kline_data_v2(
        symbol=symbol, start_date=start_date, end_date=end_date
    )
    
    if df.empty:
        return {"error": f"没有 {symbol} 的数据"}
    
    # 选择策略
    if strategy_type == "ma_cross":
        strategy = MACrossStrategy(params={
            "fast_period": fast_period,
            "slow_period": slow_period
        })
    elif strategy_type == "rsi":
        strategy = RSIStrategy(params={"period": fast_period})
    else:
        return {"error": f"未知策略: {strategy_type}"}
    
    # 回测
    engine = BacktestEngine(initial_capital=initial_capital)
    result = engine.run(df, strategy)
    
    return Response(data=result)