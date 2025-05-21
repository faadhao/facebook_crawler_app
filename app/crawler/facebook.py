from playwright.sync_api import sync_playwright
import time
import uuid
import re

def extract_post_info(post_html):
    post_url_match = re.search(r'href="(https://www.facebook.com/.+?/posts/\d+)"', post_html)
    video_url_match = re.search(r'src="([^"]+\.mp4)"', post_html)
    image_url_match = re.search(r'src="([^"]+\.jpg|\.png)"', post_html)
    reels_match = re.search(r'reels', post_html, re.IGNORECASE)

    category = "text"
    if video_url_match:
        category = "video"
    elif reels_match:
        category = "reels"
    elif image_url_match:
        category = "image"

    return {
        "uid": str(uuid.uuid4()),
        "post_url": post_url_match.group(1) if post_url_match else "",
        "video_url": video_url_match.group(1) if video_url_match else "",
        "image_url": image_url_match.group(1) if image_url_match else "",
        "comments": 0,
        "reactions": 0,
        "category": category,
    }

def crawl_facebook_posts(page_url: str, max_posts=30) -> list:
    posts_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(page_url)
        page.wait_for_timeout(5000)

        for _ in range(5):  # 滾動 5 次（可調整以達 30 則）
            page.keyboard.press("PageDown")
            time.sleep(1.5)

        html = page.content()
        raw_posts = html.split('role="article"')  # 粗略分出每則貼文

        for post_html in raw_posts:
            if len(posts_data) >= max_posts:
                break
            info = extract_post_info(post_html)
            posts_data.append(info)

        browser.close()
    return posts_data
