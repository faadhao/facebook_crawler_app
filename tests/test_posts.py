"""
貼文 API 測試
"""
import pytest
from fastapi import status
from app.models.post import Post


class TestPosts:
    """貼文相關測試"""
    
    @pytest.fixture
    def sample_posts(self, db):
        """建立範例貼文"""
        posts = [
            Post(
                uid="post-1",
                post_url="https://facebook.com/post/1",
                category="text",
                comments=10,
                reactions=50
            ),
            Post(
                uid="post-2",
                post_url="https://facebook.com/post/2",
                video_url="https://video.com/video.mp4",
                category="video",
                comments=20,
                reactions=100
            ),
            Post(
                uid="post-3",
                post_url="https://facebook.com/post/3",
                image_url="https://image.com/image.jpg",
                category="image",
                comments=5,
                reactions=25
            )
        ]
        for post in posts:
            db.add(post)
        db.commit()
        return posts
    
    def test_get_posts_from_cache(self, client, sample_posts):
        """測試從快取獲取貼文"""
        response = client.get("/posts/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "data" in data
        assert "count" in data
    
    def test_get_posts_from_database(self, client, sample_posts):
        """測試從資料庫獲取貼文"""
        response = client.get("/posts/db")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 3
        assert len(data["data"]) == 3
    
    def test_get_posts_with_category_filter(self, client, sample_posts):
        """測試類別篩選"""
        response = client.get("/posts/db?category=video")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 1
        assert data["data"][0]["category"] == "video"
    
    def test_get_posts_with_pagination(self, client, sample_posts):
        """測試分頁"""
        response = client.get("/posts/db?limit=2&offset=0")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 2
        
        response = client.get("/posts/db?limit=2&offset=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 1
    
    def test_get_categories_stats(self, client, sample_posts):
        """測試類別統計"""
        response = client.get("/posts/categories")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "categories" in data
        assert data["total"] == 3
        assert data["categories"]["video"] == 1
        assert data["categories"]["image"] == 1
        assert data["categories"]["text"] == 1
