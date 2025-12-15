"""
貼文 API 路由
處理貼文查詢相關請求
"""
from fastapi import APIRouter, Query, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.redis import redis_client
from app.core.db import get_db
from app.schemas.crawl import PostSchema
from app.services.post_service import get_posts_from_redis, get_posts_from_db
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/posts", tags=["Posts"])


@router.get("/", response_model=dict, summary="獲取貼文清單（從快取）")
async def get_posts(
    category: Optional[str] = Query(None, description="貼文類別：text/image/video/reels"),
    limit: int = Query(10, ge=1, le=100, description="返回數量限制"),
    offset: int = Query(0, ge=0, description="偏移量（用於分頁）")
):
    """
    從 Redis 快取獲取貼文清單
    
    - **category**: 可選，按類別篩選（text/image/video/reels）
    - **limit**: 返回數量限制（1-100，預設10）
    - **offset**: 偏移量，用於分頁（預設0）
    
    返回快取中的貼文數据，速度较快但可能不包含最新數据
    """
    logger.info(f"查詢貼文: category={category}, limit={limit}, offset={offset}")
    
    try:
        posts = get_posts_from_redis(
            redis_client,
            category=category,
            limit=limit,
            offset=offset
        )
        
        return {
            "data": posts,
            "count": len(posts),
            "category": category,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"獲取貼文失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取貼文失敗"
        )


@router.get("/db", response_model=dict, summary="獲取貼文清單（從資料庫）")
async def get_posts_from_database(
    category: Optional[str] = Query(None, description="貼文類別：text/image/video/reels"),
    limit: int = Query(10, ge=1, le=100, description="返回數量限制"),
    offset: int = Query(0, ge=0, description="偏移量（用於分頁）"),
    db: Session = Depends(get_db)
):
    """
    從 PostgreSQL 資料庫獲取貼文清單
    
    - **category**: 可選，按類別篩選（text/image/video/reels）
    - **limit**: 返回數量限制（1-100，預設10）
    - **offset**: 偏移量，用於分頁（預設0）
    
    返回資料庫中的完整數据，包含所有历史貼文
    """
    logger.info(f"從資料庫查詢貼文: category={category}, limit={limit}, offset={offset}")
    
    try:
        posts = get_posts_from_db(
            db,
            category=category,
            limit=limit,
            offset=offset
        )
        
        # 转换為字典清單
        posts_data = [
            {
                "uid": post.uid,
                "post_url": post.post_url,
                "video_url": post.video_url,
                "image_url": post.image_url,
                "comments": post.comments,
                "reactions": post.reactions,
                "category": post.category
            }
            for post in posts
        ]
        
        return {
            "data": posts_data,
            "count": len(posts_data),
            "category": category,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"從資料庫獲取貼文失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取貼文失敗"
        )


@router.get("/categories", summary="獲取所有貼文類別")
async def get_categories(db: Session = Depends(get_db)):
    """
    獲取資料庫中所有貼文的類別清單及其數量
    """
    try:
        from sqlalchemy import func
        from app.models.post import Post
        
        # 查詢每個類別的數量
        categories = db.query(
            Post.category,
            func.count(Post.uid).label('count')
        ).group_by(Post.category).all()
        
        result = {
            cat.category: cat.count
            for cat in categories
        }
        
        return {
            "categories": result,
            "total": sum(result.values())
        }
    except Exception as e:
        logger.error(f"獲取類別统計失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取類別统計失敗"
        )
