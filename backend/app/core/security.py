import hashlib
import hmac
import secrets
from datetime import timedelta
from typing import Any

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.time import utc_now

ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


def create_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    *,
    auth_version: int = 0,
) -> str:
    settings = get_settings()
    expire = utc_now() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )

    payload = {
        "sub": subject,
        "exp": expire,
        "type": "access",
        "auth_version": auth_version,
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    settings = get_settings()

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
    except InvalidTokenError:
        return None

    if payload.get("type") != "access":
        return None

    return payload


def decode_token(token: str) -> dict[str, Any] | None:
    return decode_access_token(token)


def create_secure_token() -> str:
    return secrets.token_urlsafe(48)


def hash_password_reset_token(token: str) -> str:
    settings = get_settings()

    return hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
