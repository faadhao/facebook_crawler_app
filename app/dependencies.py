"""
依賴注入函數
提供認證、授權等通用依賴
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User
from app.core.db import get_db
from app.services.auth import validate_token
from app.core.logger import get_logger

logger = get_logger(__name__)

# OAuth2 密碼認證方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    獲取當前認證使用者
    
    Args:
        token: JWT Token
        db: 資料庫會話
        
    Returns:
        當前使用者物件
        
    Raises:
        HTTPException: 認證失敗時拋出 401
    """
    # 驗證 Token
    username = validate_token(token)
    if not username:
        logger.warning("Token 驗證失敗")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證憑據",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 查詢使用者
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"使用者不存在: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="使用者不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    獲取當前活躍使用者（可擴展使用者狀態檢查）
    
    Args:
        current_user: 當前使用者
        
    Returns:
        當前活躍使用者物件
    """
    # 未來可以添加使用者狀態檢查，如 is_active 欄位
    return current_user


async def require_admin1_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    要求使用者必須是 admin1
    
    Args:
        current_user: 當前使用者
        
    Returns:
        當前使用者物件
        
    Raises:
        HTTPException: 權限不足時拋出 403
    """
    if current_user.username != "admin1":
        logger.warning(f"使用者 {current_user.username} 嘗試存取需要 admin1 權限的資源")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="權限不足：僅限 admin1 使用者存取"
        )
    return current_user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    獲取可選的當前使用者（用於可選認證的端點）
    
    Args:
        token: JWT Token（可選）
        db: 資料庫會話
        
    Returns:
        當前使用者物件或 None
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None
