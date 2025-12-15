"""
認證相關的 Pydantic 模型
"""
from pydantic import BaseModel, Field, validator
import re


class LoginRequest(BaseModel):
    """登入請求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="使用者名")
    password: str = Field(..., min_length=6, description="密碼")
    
    @validator('username')
    def validate_username(cls, v):
        """驗證使用者名格式"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('使用者名只能包含字母、數字和底線')
        return v


class TokenResponse(BaseModel):
    """Token 回應模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=3600, description="過期時間（秒）")


class UserResponse(BaseModel):
    """使用者資訊回應模型"""
    id: int
    username: str
    
    class Config:
        from_attributes = True
