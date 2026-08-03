from __future__ import annotations

import json
from typing import Any

from app.infrastructure.queue.base import QueueClient
from app.infrastructure.rabbitmq.client import get_rabbitmq_connection,close_rabbitmq_connection

class RabbitmqQueueClient(QueueClient):
    def __init__(self)->None:
        self._client=get_rabbitmq_connection()

    async def enqueue(self, queue_name:str, payload:dict[str,Any]):
        return await super().enqueue(queue_name, json.dumps(payload))

    