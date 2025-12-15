"""
Facebook 爬蟲應用主入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.api import auth, crawler, posts
from app.core.db import init_db
from app.core.config import settings
from app.core.logger import setup_logging, get_logger
from app.core.monitoring import prometheus_middleware, metrics_endpoint
from app.core.rate_limit import limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# 設置日誌
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用啟動和關閉時的生命週期管理"""
    # 啟動時執行
    logger.info(f"正在啟動 {settings.APP_NAME} v{settings.APP_VERSION}")
    try:
        init_db()
        logger.info("應用啟動成功")
    except Exception as e:
        logger.error(f"應用啟動失敗: {e}")
        raise
    
    yield
    
    # 關閉時執行
    logger.info("應用正在關閉")


# 創建 FastAPI 應用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="一個用於爬取和管理 Facebook 貼文的 API 服務",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置限流器
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加 Prometheus 監控中間件
app.middleware("http")(prometheus_middleware)


# 全域異常處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域異常處理器"""
    logger.error(f"未捕獲的異常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "伺服器內部錯誤",
            "message": str(exc) if settings.DEBUG else "請稍後重試"
        }
    )


# 健康檢查端點
@app.get("/", tags=["Health"])
async def root():
    """根路徑 - 健康檢查"""
    return {
@limiter.limit("30/minute")
async def health_check(request: Request):
    """健康檢查端點"""
    try:
        from app.core.redis import redis_client
        redis_client.ping()
        redis_status = "正常"
    except Exception as e:
        logger.error(f"Redis 健康檢查失敗: {e}")
        redis_status = "異常"
    
    return {
        "status": "healthy",
        "database": "正常",
        "redis": redis_status
    }


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus 監控指標端點"""
    return metrics_endpoint()   logger.error(f"Redis 健康檢查失敗: {e}")
        redis_status = "異常"
    
    return {
        "status": "healthy",
        "database": "正常",
        "redis": redis_status
    }


# 註冊路由
app.include_router(auth.router)
app.include_router(crawler.router)
app.include_router(posts.router)

logger.info("所有路由已註冊")
