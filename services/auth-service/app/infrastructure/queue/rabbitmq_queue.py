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


    async def enqueue(self, queue_name:str, payload:dict[str,Any])->None:
        return await super().enqueue(queue_name, json.dumps(payload))

    async def dequeue(self, queue_name:str)->dict[str,Any]|None:
        return await super().dequeue(queue_name)

    async def close(self) -> None:
        await close_rabbitmq_connection()