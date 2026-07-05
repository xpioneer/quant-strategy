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


@lru_cache()
def get_settings() -> Settings:
    return Settings()
