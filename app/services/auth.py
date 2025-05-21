from passlib.hash import bcrypt
from jose import jwt
import redis
import os
import uuid
from datetime import datetime, timedelta

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"))

def verify_password(plain, hashed):
    return bcrypt.verify(plain, hashed)

def get_password_hash(password):
    return bcrypt.hash(password)

def create_access_token(username: str):
    token = str(uuid.uuid4())
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire, "jti": token}
    encoded = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # 確保同一帳號只有一個 Token
    redis_client.set(f"user_token:{username}", token, ex=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    redis_client.set(f"token_user:{token}", username, ex=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    return encoded

def validate_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        jti = payload.get("jti")
        current = redis_client.get(f"user_token:{username}")
        if current and current.decode() == jti:
            return username
    except:
        pass
    return None
