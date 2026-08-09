from __future__ import annotations

import json
from typing import Any
import aio_pika
from collections.abc import Awaitable, Callable
from aio_pika import DeliveryMode, ExchangeType
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel,AbstractIncomingMessage
from app.infrastructure.queue.base import QueueClient
from app.infrastructure.rabbitmq.client import get_rabbitmq_connection,close_rabbitmq_connection
from app.infrastructure.queue.message import QueueMessage
from app.infrastructure.queue.rabbitmq_message import RabbitMQMessage
EMAIL_EXCHANGE_NAME = "email.exchange"
EMAIL_ROUTING_KEY = "email.send"

DEAD_EXCHANGE_NAME = "email.dead.exchange"
DEAD_ROUTING_KEY = "email.dead"

class RabbitMQQueueClient(QueueClient):
    def __init__(self,exchange_name: str,
        routing_key: str,)->None:
        self._connection:AbstractRobustConnection|None=None
        self._channel:AbstractRobustChannel|None=None
        self._exchange_name = exchange_name
        self._routing_key = routing_key

    async def _ensure_channel(self)->AbstractRobustChannel:
        if self._connection is None or self._connection.is_closed:
            self._connection=await get_rabbitmq_connection()
        if self._channel is None or self._channel.is_closed:
            self._channel=await self._connection.channel()
            await self._channel.set_qos(prefetch_count=1)
        return self._channel  

    async def _ensure_topology(self, queue_name: str) -> tuple[aio_pika.abc.AbstractRobustExchange, aio_pika.abc.AbstractRobustQueue]:
        channel = await self._ensure_channel()

        exchange = await channel.declare_exchange(
            self._exchange_name,
            type=ExchangeType.DIRECT,
            durable=True,
        )

        queue = await channel.declare_queue(
            queue_name,
            durable=True,
        )

        await queue.bind(exchange, routing_key=self._routing_key)
        return exchange, queue


    async def enqueue(self, queue_name: str, payload: dict[str, Any]) -> None:
        exchange, _ =await self._ensure_topology(queue_name)
        message = aio_pika.Message(
            body=json.dumps(payload).encode("utf-8"),
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
        )
        await exchange.publish(
            message,
            routing_key=self._routing_key,
        )

    async def dequeue(self, queue_name: str) -> QueueMessage | None:
        channel = await self._ensure_channel()
        queue = await channel.declare_queue(queue_name, durable=True)

        incoming = await queue.get(no_ack=False)
        if incoming is None:
            return None

        return RabbitMQMessage(incoming)

    async def close(self) -> None:
        if self._channel is not None and not self._channel.is_closed:
            await self._channel.close()
        self._channel = None

        await close_rabbitmq_connection()
        self._connection = None

    async def consume(
    self,
    queue_name: str,
    callback: Callable[[AbstractIncomingMessage], Awaitable[None]],) -> None:
        channel = await self._ensure_channel()

        exchange = await channel.declare_exchange(
            EMAIL_EXCHANGE_NAME,
            ExchangeType.DIRECT,
            durable=True,
        )

        queue = await channel.declare_queue(
            queue_name,
            durable=True,
        )

        await queue.bind(
            exchange,
            routing_key=EMAIL_ROUTING_KEY,
        )

        await queue.consume(callback)