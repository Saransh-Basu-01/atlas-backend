from __future__ import annotations

import json
from typing import Any

from aio_pika.abc import AbstractIncomingMessage

from app.infrastructure.queue.message import QueueMessage


class RabbitMQMessage(QueueMessage):
    def __init__(
        self,
        incoming_message: AbstractIncomingMessage,
    ) -> None:
        self._incoming_message = incoming_message
        self.payload: dict[str, Any] = json.loads(
            incoming_message.body.decode("utf-8")
        )

    async def ack(self) -> None:
        await self._incoming_message.ack()

    async def nack(self, requeue: bool = True) -> None:
        await self._incoming_message.nack(requeue=requeue)