"""
爬蟲相關的 Pydantic 模型
"""
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional


class CrawlRequest(BaseModel):
    """爬蟲請求模型"""
    page_url: HttpUrl = Field(..., description="Facebook 頁面 URL")
    limit: Optional[int] = Field(30, ge=1, le=100, description="最多爬取的貼文數量")
    
    @validator('page_url')
    def validate_facebook_url(cls, v):
        """驗證是否為 Facebook URL"""
        url_str = str(v)
        if 'facebook.com' not in url_str:
            raise ValueError('必須是 Facebook 的 URL')
        return v


class CrawlResponse(BaseModel):
    """爬蟲回應模型"""
    message: str
    posts_count: int
    success: bool = True


class PostSchema(BaseModel):
    """貼文數据模型"""
    uid: str
    post_url: str
    video_url: Optional[str] = None
    image_url: Optional[str] = None
    comments: int = 0
    reactions: int = 0
    category: str
    
    class Config:
        from_attributes = True
