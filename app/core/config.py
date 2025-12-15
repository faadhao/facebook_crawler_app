"""
應用配置管理
統一管理所有環境變數和配置項
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """應用配置類別"""
    
    # 基本配置
    APP_NAME: str = "Facebook Crawler API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 資料庫配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/postgres"
    )
    
    # Redis 配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = 0
    REDIS_DECODE_RESPONSES: bool = True
    
    # JWT 配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # 爬蟲配置
    CRAWLER_MAX_POSTS: int = 30
    CRAWLER_SCROLL_COUNT: int = 5
    CRAWLER_SCROLL_DELAY: float = 1.5
    CRAWLER_HEADLESS: bool = True
    CRAWLER_TIMEOUT: int = 30000  # 毫秒
    
    # Redis 快取配置
    REDIS_POST_TTL: int = 86400  # 24小時
    
    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 創建全域配置實例
settings = Settings()
