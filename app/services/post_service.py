from app.models.post import Post
from sqlalchemy.orm import Session
from redis import Redis
import json

def save_posts_to_db(db: Session, posts: list):
    for data in posts:
        if not db.query(Post).filter(Post.uid == data["uid"]).first():
            db_post = Post(**data)
            db.add(db_post)
    db.commit()

def save_posts_to_redis(redis: Redis, posts: list):
    for post in posts:
        key = f"post:{post['uid']}"
        redis.set(key, json.dumps(post))
        redis.rpush("posts:index", post["uid"])  # 可做列表查詢用
