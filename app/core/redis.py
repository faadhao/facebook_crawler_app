"""
Redis 連接管理
"""
import redis
from typing import Optional
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis 客戶端單例類別"""
    
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """獲取 Redis 客戶端實例"""
        if cls._instance is None:
            try:
                cls._instance = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=settings.REDIS_DECODE_RESPONSES,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # 測試連接
                cls._instance.ping()
                logger.info(f"Redis 連接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                logger.error(f"Redis 連接失敗: {e}")
                raise
        return cls._instance


# 創建全域 Redis 客戶端實例
redis_client = RedisClient.get_client()
