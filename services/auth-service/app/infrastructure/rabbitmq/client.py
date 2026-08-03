from __future__ import annotations

from typing import Optional

import aio_pika
from aio_pika.abc import AbstractRobustConnection

from app.core.config import settings


_rabbitmq_connection: Optional[AbstractRobustConnection] = None
#This prevents creating a new RabbitMQ connection every time another part of the application needs RabbitMQ.

async def get_rabbitmq_connection() -> AbstractRobustConnection:
    global _rabbitmq_connection

    if (
        _rabbitmq_connection is None
        or _rabbitmq_connection.is_closed
    ):
        _rabbitmq_connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL
        )

    return _rabbitmq_connection


async def close_rabbitmq_connection() -> None:
    global _rabbitmq_connection

    if (
        _rabbitmq_connection is not None
        and not _rabbitmq_connection.is_closed
    ):
        await _rabbitmq_connection.close()

    _rabbitmq_connection = None