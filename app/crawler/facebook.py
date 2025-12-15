"""
Facebook 爬蟲模組
使用 Playwright 爬取 Facebook 頁面貼文
"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from typing import List, Dict, Optional
import time
import uuid
import re
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class FacebookCrawlerError(Exception):
    """爬蟲自定義異常"""
    pass


def extract_post_info(post_html: str) -> Optional[Dict]:
    """
    從 HTML 片段提取貼文資訊
    
    Args:
        post_html: 貼文的 HTML 代碼
        
    Returns:
        包含貼文資訊的字典，如果解析失敗返回 None
    """
    try:
        post_url_match = re.search(
            r'href="(https://www\.facebook\.com/.+?/posts/\d+)"',
            post_html
        )
        video_url_match = re.search(r'src="([^"]+\.mp4)"', post_html)
        image_url_match = re.search(r'src="([^"]+\.(?:jpg|png|jpeg))"', post_html)
        reels_match = re.search(r'reels', post_html, re.IGNORECASE)

        # 如果没有找到貼文 URL，跳過这條
        if not post_url_match:
            return None

        # 判斷貼文類別型
        category = "text"
        if video_url_match:
            category = "video"
        elif reels_match:
            category = "reels"
        elif image_url_match:
            category = "image"

        return {
            "uid": str(uuid.uuid4()),
            "post_url": post_url_match.group(1),
            "video_url": video_url_match.group(1) if video_url_match else "",
            "image_url": image_url_match.group(1) if image_url_match else "",
            "comments": 0,
            "reactions": 0,
            "category": category,
        }
    except Exception as e:
        logger.warning(f"解析貼文資訊失敗: {e}")
        return None


def crawl_facebook_posts(page_url: str, max_posts: int = None) -> List[Dict]:
    """
    爬取 Facebook 頁面的貼文
    
    Args:
        page_url: Facebook 頁面的 URL
        max_posts: 最多爬取的貼文數量
        
    Returns:
        貼文數据清單
        
    Raises:
        FacebookCrawlerError: 爬蟲執行失敗時抛出
    """
    if max_posts is None:
        max_posts = settings.CRAWLER_MAX_POSTS
    
    posts_data = []
    logger.info(f"開始爬取 Facebook 頁面: {page_url}, 目標數量: {max_posts}")
    
    try:
        with sync_playwright() as p:
            # 啟動瀏覽器
            browser = p.chromium.launch(
                headless=settings.CRAWLER_HEADLESS,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # 創建上下文和頁面
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            # 設定逾時
            page.set_default_timeout(settings.CRAWLER_TIMEOUT)
            
            try:
                # 存取頁面
                logger.info(f"正在加載頁面: {page_url}")
                page.goto(str(page_url), wait_until='networkidle')
                page.wait_for_timeout(5000)
                
                # 滾動加載更多內容
                scroll_count = settings.CRAWLER_SCROLL_COUNT
                for i in range(scroll_count):
                    logger.debug(f"滾動頁面 {i+1}/{scroll_count}")
                    page.keyboard.press("PageDown")
                    time.sleep(settings.CRAWLER_SCROLL_DELAY)
                
                # 獲取頁面內容
                html = page.content()
                logger.info(f"頁面內容獲取成功，長度: {len(html)}")
                
                # 分割貼文
                raw_posts = html.split('role="article"')
                logger.info(f"找到 {len(raw_posts)} 個貼文片段")
                
                # 解析每個貼文
                for idx, post_html in enumerate(raw_posts):
                    if len(posts_data) >= max_posts:
                        break
                    
                    info = extract_post_info(post_html)
                    if info:
                        posts_data.append(info)
                        logger.debug(f"成功解析貼文 {len(posts_data)}: {info['category']}")
                
                logger.info(f"爬取完成，共獲取 {len(posts_data)} 則貼文")
                
            except PlaywrightTimeout as e:
                logger.error(f"頁面加載逾時: {e}")
                raise FacebookCrawlerError(f"頁面加載逾時: {str(e)}")
            
            finally:
                context.close()
                browser.close()
                
    except Exception as e:
        logger.error(f"爬蟲執行失敗: {e}", exc_info=True)
        raise FacebookCrawlerError(f"爬蟲執行失敗: {str(e)}")
    
    return posts_data
