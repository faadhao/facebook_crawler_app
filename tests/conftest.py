"""
Pytest 配置和共用 fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.db import Base, get_db
from app.core.redis import redis_client
import os

# 使用測試資料庫
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """建立測試資料庫會話"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """建立測試客戶端"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db):
    """建立測試使用者"""
    from app.models.user import User
    from app.services.auth import get_password_hash
    
    user = User(
        username="testuser",
        hashed_password=get_password_hash("testpass123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(db):
    """建立管理員使用者"""
    from app.models.user import User
    from app.services.auth import get_password_hash
    
    user = User(
        username="admin1",
        hashed_password=get_password_hash("1minda")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """獲取認證 Token"""
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def admin_token(client, admin_user):
    """獲取管理員 Token"""
    response = client.post(
        "/auth/login",
        json={"username": "admin1", "password": "1minda"}
    )
    return response.json()["access_token"]


@pytest.fixture(autouse=True)
def clear_redis():
    """清除 Redis 測試資料"""
    yield
    try:
        redis_client.flushdb()
    except:
        pass
