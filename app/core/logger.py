"""
日誌配置
提供統一的日誌記錄功能
"""
import logging
import sys
from pathlib import Path
from app.core.config import settings


def setup_logging():
    """配置應用日誌"""
    
    # 創建日誌目錄
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置日誌格式
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 配置根日誌記錄器
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # 清除現有的處理器
    logger.handlers.clear()
    
    # 控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # 檔案處理器
    file_handler = logging.FileHandler(
        log_dir / "app.log",
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    # 錯誤日誌檔案處理器
    error_handler = logging.FileHandler(
        log_dir / "error.log",
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    logger.addHandler(error_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """獲取指定名稱的日誌記錄器"""
    return logging.getLogger(name)
