from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings


def generate_reset_token(reset_token_bytes: int = 32) -> str:
    # Opaque, random, URL-safe token (not JWT)
    return secrets.token_urlsafe(reset_token_bytes)


def hash_reset_token(token: str) -> str:
    # Store only hash in DB (never raw reset token)
    return hashlib.sha256(token.encode("utf-8")).hexdigest()