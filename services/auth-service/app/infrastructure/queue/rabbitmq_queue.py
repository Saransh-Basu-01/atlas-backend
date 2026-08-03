from __future__ import annotations

import json
from typing import Any
import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
from app.infrastructure.queue.base import QueueClient
from app.infrastructure.rabbitmq.client import get_rabbitmq_connection,close_rabbitmq_connection

class RabbitmqQueueClient(QueueClient):
    def __init__(self)->None:
        self._connection:AbstractRobustConnection|None=None
        self._channel:AbstractRobustChannel|None=None

    async def _ensure_channel(self)->AbstractRobustChannel:
        if self._connection is None or self._connection.is_closed:
            self._connection=await get_rabbitmq_connection()
        if self._channel is None or self._channel.is_closed:
            self._channel=await self._connection.channe()
        return self._channel  


    async def enqueue(self, queue_name: str, payload: dict[str, Any]) -> None:
        channel = await self._ensure_channel()
        queue = await channel.declare_queue(queue_name, durable=True)

        message = aio_pika.Message(
            body=json.dumps(payload).encode("utf-8"),
            content_type="application/json",
        )
        await channel.default_exchange.publish(message, routing_key=queue.name)

    async def dequeue(self, queue_name: str) -> dict[str, Any] | None:
        channel = await self._ensure_channel()
        queue = await channel.declare_queue(queue_name, durable=True)

        incoming = await queue.get(no_ack=False)
        if incoming is None:
            return None

        async with incoming.process():
            return json.loads(incoming.body.decode("utf-8"))

    async def close(self) -> None:
        await close_rabbitmq_connection()