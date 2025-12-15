"""
Celery 配置
"""
from celery import Celery
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# 創建 Celery 應用
celery_app = Celery(
    "facebook_crawler",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/3"
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Taipei",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 分鐘逾時
    task_soft_time_limit=25 * 60,  # 25 分鐘軟逾時
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

logger.info("Celery 應用已初始化")
