from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings


def generate_refresh_token(refresh_token_bytes: int = 32) -> str:
    # Opaque, random, URL-safe token (not JWT)
    return secrets.token_urlsafe(refresh_token_bytes)


def hash_refresh_token(token: str) -> str:
    # Store only hash in DB (never raw refresh token)
    return hashlib.sha256(token.encode("utf-8")).hexdigest()