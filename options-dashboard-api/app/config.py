from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/options_db"
    
    # Redis for caching
    REDIS_URL: str = "redis://localhost:6379"
    
    # API Keys
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()