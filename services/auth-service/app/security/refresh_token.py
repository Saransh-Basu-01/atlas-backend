from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings

def create_access_token(
    user_id: int,
) -> str:
    secret=settings.SECRET_KEY.get_secret_value()
    ttl_minutes =settings.access_token_expire_minutes
    algorithm =settings.algorithm
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=ttl_minutes)

    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    return jwt.encode(payload, secret, algorithm=algorithm)


def generate_refresh_token(refresh_token_bytes: int = 32) -> str:
    # Opaque, random, URL-safe token (not JWT)
    return secrets.token_urlsafe(refresh_token_bytes)


def hash_refresh_token(token: str) -> str:
    # Store only hash in DB (never raw refresh token)
    return hashlib.sha256(token.encode("utf-8")).hexdigest()