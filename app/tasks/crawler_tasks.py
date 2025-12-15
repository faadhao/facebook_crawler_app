"""
Celery 異步任務
"""
from app.core.celery_app import celery_app
from app.crawler.facebook import crawl_facebook_posts, FacebookCrawlerError
from app.services.post_service import save_posts_to_db, save_posts_to_redis
from app.core.db import SessionLocal
from app.core.redis import redis_client
from app.core.logger import get_logger
from app.core.monitoring import crawler_tasks_total, crawler_posts_scraped

logger = get_logger(__name__)


@celery_app.task(bind=True, name="tasks.crawl_facebook_async")
def crawl_facebook_async(self, page_url: str, max_posts: int = 30):
    """
    異步爬取 Facebook 貼文
    
    Args:
        page_url: Facebook 頁面 URL
        max_posts: 最多爬取的貼文數量
        
    Returns:
        任務結果字典
    """
    task_id = self.request.id
    logger.info(f"開始異步爬蟲任務 {task_id}: {page_url}")
    
    try:
        # 更新任務狀態
        self.update_state(state='PROGRESS', meta={'status': '正在爬取...'})
        
        # 執行爬取
        posts = crawl_facebook_posts(page_url, max_posts)
        
        if not posts:
            crawler_tasks_total.labels(status="no_posts").inc()
            return {
                'status': 'completed',
                'posts_count': 0,
                'message': '未找到任何貼文'
            }
        
        # 儲存到資料庫
        self.update_state(state='PROGRESS', meta={'status': '正在儲存到資料庫...'})
        db = SessionLocal()
        try:
            db_count = save_posts_to_db(db, posts)
        finally:
            db.close()
        
        # 儲存到 Redis
        self.update_state(state='PROGRESS', meta={'status': '正在儲存到快取...'})
        redis_count = save_posts_to_redis(redis_client, posts)
        
        # 更新監控指標
        crawler_tasks_total.labels(status="success").inc()
        crawler_posts_scraped.inc(len(posts))
        
        result = {
            'status': 'completed',
            'posts_count': len(posts),
            'db_saved': db_count,
            'redis_saved': redis_count,
            'message': f'成功爬取 {len(posts)} 則貼文'
        }
        
        logger.info(f"異步爬蟲任務 {task_id} 完成: {result}")
        return result
        
    except FacebookCrawlerError as e:
        crawler_tasks_total.labels(status="error").inc()
        logger.error(f"異步爬蟲任務 {task_id} 失敗: {e}")
        raise
    except Exception as e:
        crawler_tasks_total.labels(status="error").inc()
        logger.error(f"異步爬蟲任務 {task_id} 發生未知錯誤: {e}", exc_info=True)
        raise


@celery_app.task(name="tasks.cleanup_old_posts")
def cleanup_old_posts():
    """
    清理過期的貼文資料（定期任務）
    """
    logger.info("開始清理過期貼文")
    try:
        # 清理 Redis 中的過期鍵
        deleted_count = 0
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match="post:*", count=100)
            for key in keys:
                if not redis_client.exists(key):
                    redis_client.zrem("posts:index", key.replace("post:", ""))
                    deleted_count += 1
            if cursor == 0:
                break
        
        logger.info(f"清理完成，刪除了 {deleted_count} 個過期貼文")
        return {'deleted_count': deleted_count}
    except Exception as e:
        logger.error(f"清理過期貼文失敗: {e}")
        raise


# Celery Beat 定期任務配置
celery_app.conf.beat_schedule = {
    'cleanup-old-posts-daily': {
        'task': 'tasks.cleanup_old_posts',
        'schedule': 86400.0,  # 每天執行一次
    },
}
