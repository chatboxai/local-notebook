import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

import config

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
REFRESH_TOKEN_EXPIRE_DAYS = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
_optional_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    refresh: bool = False,
) -> str:
    payload = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    elif refresh:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _validate_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise _credentials_exc
    except JWTError:
        raise _credentials_exc
    return username


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    return _validate_token(token)


async def get_current_user_query_or_header(
    header_token: Optional[str] = Depends(_optional_oauth2),
    query_token: Optional[str] = Query(default=None, alias="token"),
) -> str:
    token = header_token or query_token
    if not token:
        raise _credentials_exc
    return _validate_token(token)
