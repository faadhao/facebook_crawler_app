"""
Celery 任務模組
"""
from app.tasks.crawler_tasks import crawl_facebook_async, cleanup_old_posts

__all__ = ['crawl_facebook_async', 'cleanup_old_posts']
