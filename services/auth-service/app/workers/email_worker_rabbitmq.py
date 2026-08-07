#Rabbitmq email worker implementation
from __future__ import annotations
import asyncio
import logging
from typing import Any
from app.infrastructure.queue.rabbitmq_queue import RabbitMQQueueClient
from app.jobs.email_jobs import PasswordResetEmailJob, PasswordChangedEmailJob
from app.services.email_service import EmailService
from aio_pika.abc import AbstractIncomingMessage

from app.infrastructure.queue.rabbitmq_message import RabbitMQMessage

logger = logging.getLogger(__name__)


class RabbitMQEmailWorker:
    def __init__(self, email_service: EmailService) -> None:
        self.queue = RabbitMQQueueClient(
             exchange_name="email.exchange",
            routing_key="email.send"
            )
        
        self.email_service = email_service
        self._running = False

    async def process_job(self, job_data: dict[str, Any]) -> None:
        job_type = job_data.get("job_type")

        if job_type == "password_reset_email":
            job = PasswordResetEmailJob.from_dict(job_data)
            await self.email_service.send_password_reset_email(
                job.recipient_email,
                job.reset_token,
            )

        elif job_type == "password_changed_email":
            job = PasswordChangedEmailJob.from_dict(job_data)
            await self.email_service.send_password_changed_email(
                job.recipient_email
            )

        else:
            raise ValueError(f"Unknown job type: {job_type}")

    async def handle_message(self,incoming_message:AbstractIncomingMessage)->None:
        message = RabbitMQMessage(incoming_message)
        try:
            await self.process_job(message.payload)
            await message.ack()
        except Exception:
            await message.nack(requeue=True)


    async def run(self) -> None:
        self._running = True

        logger.info("RabbitMQ Email Worker started")

        try:
            await self.queue.consume(
                "email.queue",
                self.handle_message,
            )

            # Keep the worker alive while RabbitMQ invokes
            # handle_message() whenever a new message arrives.
            await asyncio.Future()

        except asyncio.CancelledError:
            logger.info("RabbitMQ Email Worker cancelled")
            raise

        finally:
            logger.info("Shutting down RabbitMQ Email Worker")
            await self.queue.close()

               
            
    async def stop(self) -> None:
        self._running = False
        await self.queue.close()

    