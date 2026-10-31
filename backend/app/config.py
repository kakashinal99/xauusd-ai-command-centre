"""Application configuration loaded from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "XAUUSD AI Command Centre"
    app_env: str = "development"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    ctrader_client_id: str = ""
    ctrader_client_secret: str = ""
    ctrader_redirect_uri: str = ""
    ctrader_access_token: str = ""
    ctrader_refresh_token: str = ""
    ctrader_account_id: str = ""
    ctrader_environment: str = "demo"
    twelve_data_api_key: str = ""
    twelve_data_symbol: str = "XAU/USD"
    twelve_data_rest_base_url: str = "https://api.twelvedata.com"
    twelve_data_ws_url: str = "wss://ws.twelvedata.com/v1/quotes/price"
    market_data_provider: str = "twelvedata"
    backend_internal_url: str = "http://localhost:8000"
    database_url: str = ""
    redis_url: str = ""
    ingest_api_key: str = ""
    jwt_secret: str = ""
    access_token_minutes: int = 30
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
