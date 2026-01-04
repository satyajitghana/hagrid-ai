from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Hagrid AI"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Market Data Config
    MARKET_DATA_PROVIDER: str = "mock"  # mock, zerodha, etc.
    
    # Trading Config
    MAX_RISK_PER_TRADE_PERCENT: float = 1.0
    MAX_DAILY_LOSS_PERCENT: float = 2.0
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()