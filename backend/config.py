"""
Configuration settings for Shopping Chat Agent Backend
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App settings
    APP_NAME: str = "Shopping Chat Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API settings
    API_PREFIX: str = "/api"
    
    # Gemini AI settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"  # Current recommended model
    
    # Database settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./phone_catalog.db"
    
    # Redis settings (for scalability)
    REDIS_URL: Optional[str] = None
    REDIS_ENABLED: bool = False
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 30
    
    # CORS settings
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Session settings
    SESSION_TTL_SECONDS: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
