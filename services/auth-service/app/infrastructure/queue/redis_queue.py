from __future__ import annotations

import json
from typing import Any

from app.infrastructure.queue.base import QueueClient
from app.infrastructure.redis.client import get_redis_client, close_redis_client

class RedisQueueClient(QueueClient):
    def __init__(self) -> None:
        self._client = get_redis_client()

    async def enqueue(self, queue_name: str, payload: dict[str, Any]) -> None:
        """
        Push a job/message onto the Redis list queue.
        """
        await self._client.lpush(queue_name, json.dumps(payload))

    async def dequeue(self, queue_name: str) -> dict[str, Any] | None:
        """
        Pop the next job/message from the Redis list queue.
        Returns None if the queue is empty.
        """
        item = await self._client.rpop(queue_name)
        if item is None:
            return None
        return json.loads(item)

    async def close(self) -> None:
        """Close the Redis client and its connection pool."""
        await close_redis_client()