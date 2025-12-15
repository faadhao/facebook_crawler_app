"""
認證服務
處理使用者認證、Token 生成和驗證
"""
from passlib.hash import bcrypt
from jose import jwt, JWTError
import uuid
from datetime import datetime, timedelta
from typing import Optional
from app.core.config import settings
from app.core.redis import redis_client
from app.core.logger import get_logger

logger = get_logger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    驗證密碼
    
    Args:
        plain_password: 明文密碼
        hashed_password: 雜湊密碼
        
    Returns:
        密碼是否匹配
    """
    try:
        return bcrypt.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"密碼驗證失敗: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    生成密碼雜湊
    
    Args:
        password: 明文密碼
        
    Returns:
        雜湊后的密碼
    """
    return bcrypt.hash(password)


def create_access_token(username: str) -> str:
    """
    創建存取令牌
    
    Args:
        username: 使用者名
        
    Returns:
        JWT Token
    """
    try:
        # 生成唯一的 token ID
        token_id = str(uuid.uuid4())
        
        # 計算過期時間
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        # 創建 payload
        payload = {
            "sub": username,
            "exp": expire,
            "jti": token_id,
            "iat": datetime.utcnow()
        }
        
        # 編碼 JWT
        encoded_jwt = jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        # 在 Redis 中儲存 Token（確保同一帳號只有一個有效 Token）
        expire_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        redis_client.set(
            f"user_token:{username}",
            token_id,
            ex=expire_seconds
        )
        redis_client.set(
            f"token_user:{token_id}",
            username,
            ex=expire_seconds
        )
        
        logger.info(f"為使用者 {username} 創建了新的存取令牌")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"創建存取令牌失敗: {e}")
        raise


def validate_token(token: str) -> Optional[str]:
    """
    驗證存取令牌
    
    Args:
        token: JWT Token
        
    Returns:
        使用者名，如果 Token 無效則返回 None
    """
    try:
        # 解碼 JWT
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        username = payload.get("sub")
        token_id = payload.get("jti")
        
        if not username or not token_id:
            logger.warning("Token payload 缺少必要欄位")
            return None
        
        # 檢查 Redis 中的 Token 是否匹配（防止 Token 被撤銷）
        stored_token_id = redis_client.get(f"user_token:{username}")
        if not stored_token_id or stored_token_id != token_id:
            logger.warning(f"Token 已失效或被撤銷: {username}")
            return None
        
        return username
        
    except JWTError as e:
        logger.warning(f"Token 驗證失敗: {e}")
        return None
    except Exception as e:
        logger.error(f"Token 驗證出錯: {e}")
        return None


def revoke_token(username: str) -> bool:
    """
    撤銷使用者的存取令牌
    
    Args:
        username: 使用者名
        
    Returns:
        是否撤銷成功
    """
    try:
        token_id = redis_client.get(f"user_token:{username}")
        if token_id:
            redis_client.delete(f"user_token:{username}")
            redis_client.delete(f"token_user:{token_id}")
            logger.info(f"已撤銷使用者 {username} 的令牌")
            return True
        return False
    except Exception as e:
        logger.error(f"撤銷令牌失敗: {e}")
        return False
