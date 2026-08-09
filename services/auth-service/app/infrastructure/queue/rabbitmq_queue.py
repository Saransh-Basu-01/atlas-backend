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

    async def _ensure_dead_topology(
            self,dead_queue_name:str
    )->tuple[aio_pika.abc.AbstractRobustExchange,aio_pika.abc.AbstractRobustQueue]:
        channel=await self._ensure_channel()
        dead_exchange=await channel.declare_exchange(
            DEAD_EXCHANGE_NAME,
            type=ExchangeType.DIRECT,
            durable=True
        )
        dead_queue=await channel.declare_queue(dead_queue_name,durable=True)
        await dead_queue.bind(dead_exchange,routing_key=DEAD_ROUTING_KEY)
        return dead_exchange,dead_queue

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

    async def move_to_dead_queue(
        self,
        message:AbstractIncomingMessage,
        dead_queue_name:str,
        payload:dict[str,Any]|None=None,
    )->None:
        dead_exchange,_=await self._ensure_dead_topology(dead_queue_name)
        body=(
            json.dumps(payload).encode('utf-8')
            if payload is not None
            else message.body
        )
        dead_message=aio_pika.Message(
                body=body,
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
                headers={
                    **(message.headers or {}),
                    "x-original-routing-key": message.routing_key,
                    "x-original-exchange": message.exchange,
                }
        )
        await dead_exchange.publish(dead_message,routing_keyy=DEAD_ROUTING_KEY)
        await message.ack()

    def get_retry_count(self, message: AbstractIncomingMessage) -> int:
        headers = message.headers or {}
        value = headers.get("x-retry-count", 0)

        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    async def retry_message(
    self, 
    message: AbstractIncomingMessage, 
    max_retries: int = 3
    )-> bool:
        """Returns True if retried, False if max retries exceeded."""
        
        current_retry_count = self.get_retry_count(message)
        
        if current_retry_count + 1>= max_retries:
            # We tried enough times, send to the graveyard!
            return False
        
        # We still have retries left! Publish it back to the main exchange
        exchange, _ = await self._ensure_topology("email.queue")
        
        # Create the new message, INCREMENTING the header counter
        retried_message = aio_pika.Message(
            body=message.body,
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
            headers={
                **(message.headers or {}),             # Keep existing headers
                "x-retry-count": current_retry_count + 1 # Increment!
            }
        )
        
        await exchange.publish(retried_message, routing_key=self._routing_key)
        await message.ack() # Ack the original delivery so RabbitMQ doesn't redeliver it
        
        return True