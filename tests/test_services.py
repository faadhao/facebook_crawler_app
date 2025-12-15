"""
服務層測試
"""
import pytest
from app.services.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    validate_token
)


class TestAuthService:
    """認證服務測試"""
    
    def test_password_hashing(self):
        """測試密碼雜湊"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)
    
    def test_create_access_token(self):
        """測試建立 Token"""
        username = "testuser"
        token = create_access_token(username)
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_validate_token(self):
        """測試驗證 Token"""
        username = "testuser"
        token = create_access_token(username)
        
        # 驗證有效 Token
        validated_username = validate_token(token)
        assert validated_username == username
        
        # 驗證無效 Token
        invalid_username = validate_token("invalid.token.here")
        assert invalid_username is None


class TestPostService:
    """貼文服務測試"""
    
    def test_save_posts_to_db(self, db):
        """測試儲存貼文到資料庫"""
        from app.services.post_service import save_posts_to_db
        from app.models.post import Post
        
        posts_data = [
            {
                "uid": "test-1",
                "post_url": "https://facebook.com/test/1",
                "category": "text",
                "comments": 0,
                "reactions": 0,
                "video_url": "",
                "image_url": ""
            }
        ]
        
        count = save_posts_to_db(db, posts_data)
        assert count == 1
        
        # 驗證資料已儲存
        post = db.query(Post).filter(Post.uid == "test-1").first()
        assert post is not None
        assert post.category == "text"
        
        # 重複儲存不應增加數量
        count = save_posts_to_db(db, posts_data)
        assert count == 0
