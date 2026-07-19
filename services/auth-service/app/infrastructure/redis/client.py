# infrastructure/redis/client.py

from __future__ import annotations

from functools import lru_cache

import redis.asyncio as redis
from app.core.config import settings

class RedisConfigError(RuntimeError):
    """Raised when Redis configuration is invalid or missing."""

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

    return client


async def close_redis_client() -> None:
    """Close the cached Redis client connection pool."""
    # Check if client exists in cache without creating it
    if get_redis_client.cache_info().currsize>0:
        client = get_redis_client()
        await client.aclose()
        get_redis_client.cache_clear()