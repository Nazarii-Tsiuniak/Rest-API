import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-change-me-change-me-change-me")
ALGORITHM = "HS256"

_USERS = {
    "admin": "admin",
}

_security = HTTPBearer()


def authenticate_user(username: str, password: str) -> bool:
    return _USERS.get(username) == password


def _create_token(username: str, token_type: str, expires_delta: timedelta) -> str:
    expire_at = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": username,
        "type": token_type,
        "exp": expire_at,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(username: str) -> str:
    return _create_token(username, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(username: str) -> str:
    return _create_token(username, "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))


def verify_token(token: str, token_type: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    if payload.get("type") != token_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    return username


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> str:
    return verify_token(credentials.credentials, "access")
