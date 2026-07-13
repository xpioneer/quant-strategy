import json
import re
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from humps.camel import case as camel_case
from loguru import logger
from datetime import datetime, timezone
from app.config.settings import get_settings
from app.common.dashboard import router as dashboard_router
from app.utils.tools import is_skip_path
from app.market.api import router as market_router
from app.indicator.api import router as indicator_router
from app.strategy.api import router as strategy_router
from app.backtest.api import router as backtest_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

try:
    from app.database import Base, engine, ensure_kline_columns
    Base.metadata.create_all(bind=engine)
    ensure_kline_columns()
    logger.info("数据库初始化成功")
except Exception as e:
    logger.warning(f"数据库初始化失败（可以稍后配置）: {e}")

app.include_router(dashboard_router, prefix=f"{settings.api_prefix}/dashboard", tags=["dashboard"])
app.include_router(market_router, prefix=f"{settings.api_prefix}/market", tags=["market"])
app.include_router(indicator_router, prefix=f"{settings.api_prefix}/indicator", tags=["indicator"])
app.include_router(strategy_router, prefix=f"{settings.api_prefix}/strategy", tags=["strategy"])
app.include_router(backtest_router, prefix=f"{settings.api_prefix}/backtest", tags=["backtest"])


@app.middleware("http")
async def camelize_response_keys(request: Request, call_next):
    # 检查路径是否需要跳过
    path = request.url.path
    if is_skip_path(path):
        return await call_next(request)  # 跳过转换
    
    response = await call_next(request)
    content_type = response.headers.get("content-type", "")
    if "application/json" not in content_type:
        return response

    body = None
    if hasattr(response, "body"):
        body = response.body
    else:
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

    if not body:
        return response

    try:
        payload = json.loads(body)
    except Exception:
        return response

    def camelize_data(value):
        if isinstance(value, dict):
            return {camel_case(k): camelize_data(v) for k, v in value.items()}
        if isinstance(value, list):
            return [camelize_data(item) for item in value]
        return value

    camelized = camelize_data(payload)
    headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
    return JSONResponse(content=camelized, status_code=response.status_code, headers=headers)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "msg": str(exc),
            "data": None
        }
    )


@app.get("/")
async def root():
    return {
        "status": 200,
        "msg": "success",
        "data": {
            "app_name": settings.app_name,
            "version": settings.app_version,
            "status": "running"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": 200,
        "msg": "success",
        "data": {
            "status": "healthy",
            "time": datetime.now()
        }
    }


def main():
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8120,
        reload=settings.debug
    )


if __name__ == "__main__":
    main()
