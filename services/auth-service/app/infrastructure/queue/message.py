from __future__ import annotations
from typing import Optional,Any
from abc import ABC,abstractmethod

class QueueMessage(ABC):
    payload:dict[str,Any]

    @abstractmethod
    async def ack(self)->None:
        raise NotImplementedError

    @abstractmethod
    async def nack(self,requeue: bool = True)->None:
        raise NotImplementedError