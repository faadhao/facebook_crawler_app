"""
API 限流中間件
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.logger import get_logger

logger = get_logger(__name__)

# 創建限流器
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri="redis://redis:6379/1",
    strategy="fixed-window"
)

# 限流規則
RATE_LIMITS = {
    "default": "100/minute",
    "auth": "10/minute",
    "crawler": "5/hour",
    "posts": "200/minute"
}


def get_rate_limit(endpoint_type: str = "default") -> str:
    """獲取特定端點的限流規則"""
    return RATE_LIMITS.get(endpoint_type, RATE_LIMITS["default"])
