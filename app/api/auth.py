"""
認證 API 路由
處理使用者登入、登出等認證相关請求
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.models.user import User
from app.core.db import get_db
from app.services import auth
from app.dependencies import get_current_user
from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, summary="使用者登入")
async def login(
    req: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    使用者登入介面
    
    - **username**: 使用者名（3-50個字元，只能包含字母、數字和底線）
    - **password**: 密碼（最少6個字元）
    
    返回 JWT Token，用於後續 API 調用的認證
    """
    logger.info(f"使用者登入嘗試: {req.username}")
    
    # 查詢使用者
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        logger.warning(f"登入失敗：使用者不存在 - {req.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="使用者名或密碼錯誤"
        )
    
    # 驗證密碼
    if not auth.verify_password(req.password, user.hashed_password):
        logger.warning(f"登入失敗：密碼錯誤 - {req.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="使用者名或密碼錯誤"
        )
    
    # 創建存取令牌
    try:
        token = auth.create_access_token(user.username)
        logger.info(f"使用者登入成功: {req.username}")
        return TokenResponse(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except Exception as e:
        logger.error(f"創建令牌失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登入失敗，請稍後重試"
        )


@router.post("/logout", summary="使用者登出")
async def logout(current_user: User = Depends(get_current_user)):
    """
    使用者登出介面
    
    撤銷當前使用者的存取令牌
    """
    logger.info(f"使用者登出: {current_user.username}")
    
    try:
        auth.revoke_token(current_user.username)
        return {"message": "登出成功"}
    except Exception as e:
        logger.error(f"登出失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失敗"
        )


@router.get("/me", response_model=UserResponse, summary="獲取當前使用者資訊")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    獲取當前登入使用者的資訊
    
    需要提供有效的認證令牌
    """
    return current_user
