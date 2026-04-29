import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    hashed: bytes = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()


def verify_password(plain: str, hashed: str) -> bool:
    result: bool = bcrypt.checkpw(plain.encode(), hashed.encode())
    return result


def create_access_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": user_id, "type": "access", "exp": expire}
    token: str = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """Return (token_jwt, jti). Store hash_password(jti) in the database."""
    jti = secrets.token_urlsafe(32)
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload: dict[str, Any] = {
        "sub": user_id,
        "jti": jti,
        "type": "refresh",
        "exp": expire,
    }
    token: str = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def decode_access_token(token: str) -> str:
    """Return the user_id (sub). Raises JWTError if invalid or wrong type."""
    payload: dict[str, Any] = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    if payload.get("type") != "access":
        raise JWTError("Not an access token")
    return str(payload["sub"])


def decode_refresh_token(token: str) -> tuple[str, str]:
    """Return (user_id, jti). Raises JWTError if invalid or wrong type."""
    payload: dict[str, Any] = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    if payload.get("type") != "refresh":
        raise JWTError("Not a refresh token")
    return str(payload["sub"]), str(payload["jti"])
