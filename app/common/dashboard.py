from fastapi import APIRouter

from app.common.schemas import Response

router = APIRouter()


@router.get("/overview")
def get_dashboard_overview():
    return Response(data={
        "total_symbols": 5,
        "active_strategies": 3,
        "last_backtest": "今日 00:00",
        "health": "ok",
    })
