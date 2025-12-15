"""
爬蟲 API 路由
處理 Facebook 爬蟲相關請求
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from app.schemas.crawl import CrawlRequest, CrawlResponse
from app.models.user import User
from app.core.db import get_db
from app.core.redis import redis_client
from app.services.post_service import save_posts_to_db, save_posts_to_redis
from app.crawler.facebook import crawl_facebook_posts, FacebookCrawlerError
from app.dependencies import require_admin1_user
from app.core.logger import get_logger
from app.core.rate_limit import limiter
from app.tasks.crawler_tasks import crawl_facebook_async
from celery.result import AsyncResult

logger = get_logger(__name__)
router = APIRouter(prefix="/crawler", tags=["Crawler"])


@router.post("/crawl", response_model=CrawlResponse, summary="爬取 Facebook 貼文")
async def crawl_posts(
    req: CrawlRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin1_user)
):
    """
    爬取指定 Facebook 頁面的貼文
    
    **權限要求：** 僅限 admin1 使用者
    
    - **page_url**: Facebook 頁面 URL（必須是有效的 Facebook URL）
    - **limit**: 最多爬取的貼文數量（1-100，預設30）
    
    爬取的數据会同時儲存到 PostgreSQL 和 Redis 快取中
    """
    logger.info(f"使用者 {current_user.username} 請求爬取: {req.page_url}")
    
    # 爬取貼文
    try:
        posts = crawl_facebook_posts(str(req.page_url), req.limit)
        
        if not posts:
            logger.warning(f"未爬取到任何貼文: {req.page_url}")
            return CrawlResponse(
                message="爬取完成，但未找到任何貼文",
                posts_count=0,
                success=True
            )
        
    except FacebookCrawlerError as e:
        logger.error(f"爬蟲執行失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"爬取失敗: {str(e)}"
        )
    except Exception as e:
        logger.error(f"爬取過程出现未知錯誤: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="爬取失敗，請稍後重試"
        )
    
    # 儲存到資料庫
    try:
        db_count = save_posts_to_db(db, posts)
        logger.info(f"已儲存 {db_count} 條新貼文到資料庫")
    except Exception as e:
        logger.error(f"儲存到資料庫失敗: {e}")
        # 繼續執行，嘗試儲存到 Redis
    
    # 儲存到 Redis
    try:
        redis_count = save_posts_to_redis(redis_client, posts)
        logger.info(f"已儲存 {redis_count} 條貼文到 Redis")
    except Exception as e:
        logger.error(f"儲存到 Redis 失敗: {e}")
        # Redis 失敗不影响整體流程
    
    return CrawlResponse(
        message=f"已成功爬取 {len(posts)} 則貼文并儲存",
        posts_count=len(posts),
        success=True
    )


@router.post("/crawl/async", summary="異步爬取 Facebook 貼文")
@limiter.limit("5/hour")
async def crawl_posts_async(
    request: Request,
    req: CrawlRequest,
    current_user: User = Depends(require_admin1_user)
):
    """
    異步爬取指定 Facebook 頁面的貼文（使用 Celery 背景任務）
    
    **權限要求：** 僅限 admin1 使用者
    **限流：** 每小時最多 5 次
    
    - **page_url**: Facebook 頁面 URL
    - **limit**: 最多爬取的貼文數量（1-100，預設30）
    
    返回任務 ID，可用於查詢任務狀態
    """
    logger.info(f"使用者 {current_user.username} 請求異步爬取: {req.page_url}")
    
    try:
        # 提交異步任務
        task = crawl_facebook_async.delay(str(req.page_url), req.limit)
        
        return {
            "task_id": task.id,
            "status": "已提交",
            "message": "爬蟲任務已提交，請使用 task_id 查詢進度"
        }
    except Exception as e:
        logger.error(f"提交異步任務失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="提交任務失敗"
        )


@router.get("/task/{task_id}", summary="查詢異步任務狀態")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(require_admin1_user)
):
    """
    查詢異步爬蟲任務的執行狀態
    
    **權限要求：** 僅限 admin1 使用者
    """
    try:
        task = AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": task.state,
        }
        
        if task.state == 'PENDING':
            response["message"] = "任務等待中"
        elif task.state == 'PROGRESS':
            response["message"] = task.info.get('status', '執行中')
        elif task.state == 'SUCCESS':
            response["result"] = task.result
        elif task.state == 'FAILURE':
            response["error"] = str(task.info)
        
        return response
    except Exception as e:
        logger.error(f"查詢任務狀態失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢失敗"
        )


@router.get("/status", summary="獲取爬蟲狀態")
@limiter.limit("30/minute")
async def get_crawler_status(
    request: Request,
    current_user: User = Depends(require_admin1_user)
):
    """
    獲取爬蟲系統的狀態資訊
    
    **權限要求：** 僅限 admin1 使用者
    """
    try:
        # 獲取 Redis 中快取的貼文數量
        cached_count = redis_client.zcard("posts:index")
        
        return {
            "status": "運行中",
            "cached_posts": cached_count,
            "message": "爬蟲系統正常"
        }
    except Exception as e:
        logger.error(f"獲取爬蟲狀態失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取狀態失敗"
        )
