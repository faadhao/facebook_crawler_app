from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.services.auth import validate_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    username = validate_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return username
