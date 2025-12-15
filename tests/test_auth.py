"""
認證 API 測試
"""
import pytest
from fastapi import status


class TestAuth:
    """認證相關測試"""
    
    def test_login_success(self, client, test_user):
        """測試成功登入"""
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "testpass123"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_username(self, client):
        """測試無效使用者名稱"""
        response = client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "password"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_invalid_password(self, client, test_user):
        """測試無效密碼"""
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_validation(self, client):
        """測試輸入驗證"""
        # 使用者名稱太短
        response = client.post(
            "/auth/login",
            json={"username": "ab", "password": "password123"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # 密碼太短
        response = client.post(
            "/auth/login",
            json={"username": "testuser", "password": "12345"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_current_user(self, client, auth_token):
        """測試獲取當前使用者資訊"""
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "testuser"
    
    def test_get_current_user_no_token(self, client):
        """測試未提供 Token"""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_logout(self, client, auth_token):
        """測試登出"""
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # 登出後 Token 應該失效
        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
