"""
貼文服務
處理貼文的儲存和查詢
"""
from app.models.post import Post
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from redis import Redis
from typing import List, Dict, Optional
import json
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def save_posts_to_db(db: Session, posts: List[Dict]) -> int:
    """
    将貼文儲存到資料庫
    
    Args:
        db: 資料庫會話
        posts: 貼文數据清單
        
    Returns:
        成功儲存的貼文數量
    """
    saved_count = 0
    try:
        for data in posts:
            try:
                # 檢查是否已存在
                existing = db.query(Post).filter(Post.uid == data["uid"]).first()
                if not existing:
                    db_post = Post(**data)
                    db.add(db_post)
                    saved_count += 1
                else:
                    logger.debug(f"貼文已存在，跳過: {data['uid']}")
            except Exception as e:
                logger.error(f"儲存單條貼文失敗: {e}, 數据: {data}")
                continue
        
        db.commit()
        logger.info(f"成功儲存 {saved_count} 條貼文到資料庫")
        return saved_count
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"資料庫儲存失敗: {e}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"儲存貼文到資料庫時出錯: {e}")
        raise


def save_posts_to_redis(redis: Redis, posts: List[Dict]) -> int:
    """
    将貼文儲存到 Redis 快取
    
    Args:
        redis: Redis 客戶端
        posts: 貼文數据清單
        
    Returns:
        成功儲存的貼文數量
    """
    saved_count = 0
    try:
        for post in posts:
            try:
                key = f"post:{post['uid']}"
                # 設定带過期時間的快取
                redis.setex(
                    key,
                    settings.REDIS_POST_TTL,
                    json.dumps(post, ensure_ascii=False)
                )
                # 添加到索引清單（使用 ZADD 可以按時間排序）
                redis.zadd("posts:index", {post['uid']: post.get('timestamp', 0)})
                saved_count += 1
            except Exception as e:
                logger.error(f"儲存單條貼文到 Redis 失敗: {e}, 數据: {post}")
                continue
        
        logger.info(f"成功儲存 {saved_count} 條貼文到 Redis")
        return saved_count
        
    except Exception as e:
        logger.error(f"儲存貼文到 Redis 時出錯: {e}")
        raise


def get_posts_from_redis(
    redis: Redis,
    category: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> List[Dict]:
    """
    從 Redis 獲取貼文
    
    Args:
        redis: Redis 客戶端
        category: 貼文類別別過濾
        limit: 返回數量限制
        offset: 偏移量
        
    Returns:
        貼文清單
    """
    try:
        # 獲取索引中的 UID（按分數倒序）
        uids = redis.zrevrange("posts:index", offset, offset + limit * 2 - 1)
        results = []
        
        for uid in uids:
            if len(results) >= limit:
                break
            
            data = redis.get(f"post:{uid}")
            if not data:
                # 如果快取過期，從索引中刪除
                redis.zrem("posts:index", uid)
                continue
            
            try:
                post = json.loads(data)
                # 類別別過濾
                if category and post.get("category") != category:
                    continue
                results.append(post)
            except json.JSONDecodeError as e:
                logger.error(f"解析貼文數据失敗: {e}, UID: {uid}")
                continue
        
        logger.info(f"從 Redis 獲取了 {len(results)} 條貼文")
        return results
        
    except Exception as e:
        logger.error(f"從 Redis 獲取貼文時出錯: {e}")
        return []


def get_posts_from_db(
    db: Session,
    category: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
) -> List[Post]:
    """
    從資料庫獲取貼文
    
    Args:
        db: 資料庫會話
        category: 貼文類別別過濾
        limit: 返回數量限制
        offset: 偏移量
        
    Returns:
        貼文清單
    """
    try:
        query = db.query(Post)
        
        if category:
            query = query.filter(Post.category == category)
        
        posts = query.offset(offset).limit(limit).all()
        logger.info(f"從資料庫獲取了 {len(posts)} 條貼文")
        return posts
        
    except Exception as e:
        logger.error(f"從資料庫獲取貼文時出錯: {e}")
        return []
