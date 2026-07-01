from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MercadoScope"
    app_version: str = "1.0.0"
    environment: str = "development"
    database_url: str = "sqlite:///./data/mercadoscope.db"
    default_tenant_slug: str = "demo-store"
    scraper_provider: str = "mock"
    scraping_enabled: bool = False
    meli_access_token: str = ""
    max_pages_hard_limit: int = 10
    request_delay_seconds: float = 2.0
    user_agent: str = "MercadoScopePortfolioBot/1.0 (+https://example.com/contact)"
    reports_dir: Path = Path("./data/reports")
    exports_dir: Path = Path("./data/exports")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.exports_dir.mkdir(parents=True, exist_ok=True)
    Path("./data").mkdir(parents=True, exist_ok=True)
    return settings
