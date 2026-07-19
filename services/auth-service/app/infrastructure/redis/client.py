# infrastructure/redis/client.py

from __future__ import annotations

from functools import lru_cache

import redis
from app.core.config import settings


class RedisConfigError(RuntimeError):
    """Raised when Redis configuration is invalid or missing."""


# def _get_redis_url() -> str:
#     """
#     Read the Redis URL from environment variables.

#     Priority:
#       1. REDIS_URL
#       2. REDIS_HOST + REDIS_PORT + REDIS_DB
#     """
#     redis_url = settings.REDIS_URL
#     if redis_url:
#         return redis_url

#     host = settings.REDIS_HOST
#     port = settings.REDIS_PORT
#     db = settings.REDIS_DB

#     if not host:
#         raise RedisConfigError(
#             "Redis configuration missing. Set REDIS_URL or REDIS_HOST."
#         )

#     return f"redis://{host}:{port}/{db}"


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    """
    Return a cached Redis client instance.

    Business logic should call this function instead of constructing
    Redis connections directly.
    """
    redis_url = settings.REDIS_URL

    client = redis.Redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        health_check_interval=30,
        retry_on_timeout=True,
    )

    # Validate connection early
    try:
        client.ping()
    except redis.RedisError as exc:
        raise RedisConfigError(f"Failed to connect to Redis: {exc}") from exc

    return client


def close_redis_client() -> None:
    """Close the cached Redis client connection pool."""
    client = get_redis_client()
    client.connection_pool.disconnect()
    get_redis_client.cache_clear()