from fastapi import APIRouter, Query, Body
from loguru import logger
from enum import Enum
from app.common.schemas import Response
from .backtest import BacktestEngine
from .strategies.ma_cross import MACrossStrategy
from .strategies.macd import MACDStrategy
from .strategies.vwap import VWAPStrategy
from .strategies.rsi import RSIStrategy
from .strategies.z_score import ZScoreStrategy
from .strategies.bollinger import BollingerStrategy
from .strategies.turtle import TurtleStrategy
from .strategies.double_bottom import DoubleBottomStrategy
from ..market.service import MarketService

router = APIRouter()

class StrategyType(str, Enum):
    """策略类型枚举（继承 str 使其可 JSON 序列化）"""
    MA_CROSS = "ma_cross"
    MACD = "macd"
    VWAP = "vwap"
    RSI = "rsi"
    Z_SCORE = "z_score"
    BOLLINGER_BANDS = "bollinger_bands"
    TURTLE = "turtle"
    DOUBLE_BOTTOM = "double_bottom"


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
    params: dict = Body({}, description="策略参数"),
    fast_period: int = Body(5, ge=2, le=100),
    slow_period: int = Body(20, ge=5, le=200),
    start_date: str = Body(None),
    end_date: str = Body(None),
    initial_capital: float = Body(100000.0, ge=1000)
):
    """运行策略回测"""
    # 获取 K 线数据
    market_service = MarketService()
    df, is_local = market_service.get_kline_data(
        symbol=symbol, start_date=start_date, end_date=end_date
    )
    
    if df.empty:
        return {"error": f"没有 {symbol} 的数据"}
    
    strategy = _get_strategy_instance(strategy_type, params)
    
    # 回测
    engine = BacktestEngine(initial_capital=initial_capital)
    result = engine.run(df, strategy)
    
    return Response(data=result)

def _get_strategy_instance(strategy_type: str, params: dict):
    """辅助工厂方法：根据类型实例化策略"""
    mapping = {
        StrategyType.MA_CROSS: lambda p: MACrossStrategy(params={
            "fast_period": p.get("fast_period", 5), 
            "slow_period": p.get("slow_period", 20)
        }),
        StrategyType.MACD: lambda p: MACDStrategy(params={"fast": p.get("fast", 12)}),
        StrategyType.VWAP: lambda p: VWAPStrategy(params={"period": p.get("period", 20)}),
        StrategyType.RSI: lambda p: RSIStrategy(params={"period": p.get("period", 14)}),
        StrategyType.Z_SCORE: lambda p: ZScoreStrategy(params={"period": p.get("period", 20)}),
        StrategyType.BOLLINGER_BANDS: lambda p: BollingerStrategy(params={"period": p.get("period", 20)}),
        StrategyType.TURTLE: lambda p: TurtleStrategy(params={"period": p.get("period", 20)}),
        StrategyType.DOUBLE_BOTTOM: lambda p: DoubleBottomStrategy(params={"period": p.get("period", 30)}),
    }
    if strategy_type not in mapping:
        raise ValueError(f"未知策略: {strategy_type}")
    return mapping[strategy_type](params)

@router.post("/compare", response_model=Response[list])
def compare_strategies(
    symbol: str = Body(..., description="股票代码"),
    start_date: str = Body(None),
    end_date: str = Body(None),
    initial_capital: float = Body(100000.0)
):
    """多策略对比回测"""
    market_service = MarketService()
    df, _ = market_service.get_kline_data(symbol=symbol, start_date=start_date, end_date=end_date)
    
    if df.empty:
        return Response(status=400, msg="无数据")

    comparison_results = []
    engine = BacktestEngine(initial_capital=initial_capital)
    all_types = [t.value for t in StrategyType.__members__.values()]
    
    for s_type in all_types:
        try:
            strategy = _get_strategy_instance(s_type, {})
            
            # 运行回测
            result = engine.run(df, strategy)
            comparison_results.append({
                "strategy": s_type,
                "total_return": result["total_return"],
                "sharpe_ratio": result["sharpe_ratio"],
                "max_drawdown": result["max_drawdown"],
                "total_trades": result["total_trades"]
            })
        except Exception as e:
            logger.error(f"策略 {s_type} 回测失败: {e}")
            comparison_results.append({
                "strategy": s_type,
                "error": str(e)
            })

    return Response(data=comparison_results)
