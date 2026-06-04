"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # ── App ──
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    signal_engine_version: str = "v1.0.0"

    # ── Database ──
    database_url: str = "postgresql+asyncpg://oil_user:oil_pass@localhost:5432/oil_desk"

    # ── Redis ──
    redis_url: str = "redis://localhost:6379/0"

    # ── API Keys ──
    eia_api_key: str = ""
    fred_api_key: str = ""
    twelvedata_api_key: str = ""

    # ── FinBERT ──
    finbert_service_url: str = "http://finbert-service:8001"

    # ── Observability ──
    prometheus_enabled: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
