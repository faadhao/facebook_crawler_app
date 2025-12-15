"""
資料庫配置和連接管理
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from typing import Generator
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)

# 創建資料庫引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 自動檢測斷開的連接
    pool_size=10,  # 連接池大小
    max_overflow=20,  # 最大溢出連接數
    echo=settings.DEBUG  # 調試模式下顯示 SQL
)

# 創建會話工廠
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 創建基類
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    獲取資料庫會話的依賴注入函數
    
    Yields:
        Session: 資料庫會話物件
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"資料庫會話錯誤: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """初始化資料庫表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("資料庫表初始化成功")
    except Exception as e:
        logger.error(f"資料庫表初始化失敗: {e}")
        raise