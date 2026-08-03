from __future__ import annotations
import aio_pika
from typing import Optional
from aio_pika.abc import AbstractRobustConnection

from app.core.config import settings

_rabbitmq_connection: Optional[AbstractRobustConnection] = None

async def get_rabbitmq_connenction()->AbstractRobustConnection:
    global _rabbitmq_connection
    if _rabbitmq_connection is None or _rabbitmq_connection.is_closed:
        _rabbitmq_connection=await aio_pika.connect_robust(
            settings.RABBITMQ_URL
        )
    return _rabbitmq_connection