from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.crawl import CrawlRequest
from app.dependencies import get_current_user
from app.models.user import User
from app.core.db import SessionLocal
from app.core.redis import redis_client
from app.services.post_service import save_posts_to_db, save_posts_to_redis
from app.crawler.facebook import crawl_facebook_posts
from app.dependencies import require_admin1_user

router = APIRouter()

@router.post("/crawl")
def crawl_posts(req: CrawlRequest, current_user: User = Depends(require_admin1_user)):
    try:
        posts = crawl_facebook_posts(req.page_url, req.limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬取失敗: {e}")

    db = SessionLocal()
    try:
        save_posts_to_db(db, posts)
    finally:
        db.close()

    save_posts_to_redis(redis_client, posts)

    return {"message": f"已爬取 {len(posts)} 則貼文並儲存"}
