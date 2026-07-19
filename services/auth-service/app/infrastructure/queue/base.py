# app/infrastructure/queue/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class QueueClient(ABC):
    """
    Base interface for queue implementations.
    """

    @abstractmethod
    async def enqueue(self, queue_name: str, payload: dict[str, Any]) -> None:
        """
        Add a job/message to the queue.
        """
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """
        Close the queue client and release resources.
        """
        raise NotImplementedError
    
    @abstractmethod
    async def dequeue(self, queue_name: str) -> dict[str, Any] | None:
        """
        Remove and return the next job/message from the queue.
        Returns None if the queue is empty.
        """
        raise NotImplementedError