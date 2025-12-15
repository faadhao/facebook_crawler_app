"""
Prometheus 監控中間件和指標
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse
import time
from app.core.logger import get_logger

logger = get_logger(__name__)

# 定義監控指標
http_requests_total = Counter(
    'http_requests_total',
    'HTTP 請求總數',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP 請求耗時（秒）',
    ['method', 'endpoint']
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    '進行中的 HTTP 請求數量',
    ['method', 'endpoint']
)

crawler_tasks_total = Counter(
    'crawler_tasks_total',
    '爬蟲任務總數',
    ['status']
)

crawler_posts_scraped = Counter(
    'crawler_posts_scraped',
    '已爬取的貼文總數'
)

redis_operations_total = Counter(
    'redis_operations_total',
    'Redis 操作總數',
    ['operation', 'status']
)

database_queries_total = Counter(
    'database_queries_total',
    '資料庫查詢總數',
    ['operation', 'status']
)


async def prometheus_middleware(request: Request, call_next):
    """Prometheus 監控中間件"""
    method = request.method
    path = request.url.path
    
    # 忽略 metrics 端點本身
    if path == "/metrics":
        return await call_next(request)
    
    # 增加進行中的請求計數
    http_requests_in_progress.labels(method=method, endpoint=path).inc()
    
    # 記錄開始時間
    start_time = time.time()
    
    try:
        # 執行請求
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        logger.error(f"請求處理異常: {e}")
        status_code = 500
        raise
    finally:
        # 計算請求耗時
        duration = time.time() - start_time
        
        # 記錄指標
        http_requests_total.labels(
            method=method,
            endpoint=path,
            status=status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=path
        ).observe(duration)
        
        # 減少進行中的請求計數
        http_requests_in_progress.labels(method=method, endpoint=path).dec()
    
    return response


def metrics_endpoint() -> Response:
    """返回 Prometheus 指標"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
