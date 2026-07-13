from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Stock Quant Strategy"
    app_version: str = "1.0.0"
    debug: bool = True

    database_url: str = "sqlite:///./storage/stock_quant.db"
    redis_url: str = "redis://localhost:6379/0"

    api_prefix: str = "/api/v1"

    tushare_token: str = ""

    model_config = SettingsConfigDict(env_file=".env")

# 不需要转换的路径规则
SKIP_PATH_PATTERNS: list[str] = [
    r"^/docs",         # Swagger 文档
    r"^/redoc",        # ReDoc 文档
    r"^/openapi\.json", # OpenAPI 规范
]

@lru_cache()
def get_settings() -> Settings:
    return Settings()
