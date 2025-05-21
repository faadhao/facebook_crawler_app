from fastapi import APIRouter, Query
from typing import List, Optional
from app.core.redis import redis_client
import json

router = APIRouter()

@router.get("/posts")
def get_cached_posts(category: Optional[str] = Query(None), limit: int = 10):
    keys = redis_client.lrange("posts:index", 0, -1)
    results = []

    for uid in keys:
        data = redis_client.get(f"post:{uid}")
        if not data:
            continue
        post = json.loads(data)
        if category and post["category"] != category:
            continue
        results.append(post)
        if len(results) >= limit:
            break

    return {"data": results, "count": len(results)}
