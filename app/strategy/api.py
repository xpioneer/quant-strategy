from fastapi import APIRouter
from loguru import logger
from app.common.schemas import Response

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
