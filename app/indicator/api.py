from fastapi import APIRouter
from loguru import logger
from app.market.service import MarketService
from app.indicator.calculator import IndicatorCalculator

router = APIRouter()
market_service = MarketService()
indicator_calculator = IndicatorCalculator()


@router.get("/indicators/{symbol}")
def get_indicators(
    symbol: str,
    start_date: str,
    end_date: str,
    period: str = "daily"
):
    logger.info(f"获取指标数据: {symbol}")
    df = market_service.get_kline_data(symbol, start_date, end_date, period)
    df_with_indicators = indicator_calculator.calculate_all(df)
    df_with_indicators = df_with_indicators.reset_index()
    df_with_indicators['date'] = df_with_indicators['date'].astype(str)
    return {
        "status": 200,
        "msg": "success",
        "data": {
            'data': df_with_indicators.to_dict('records'),
            'columns': list(df_with_indicators.columns)
        }
    }
