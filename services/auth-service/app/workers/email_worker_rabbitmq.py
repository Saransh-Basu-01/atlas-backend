#Rabbitmq email worker implementation
from __future__ import annotations
import asyncio
import logging
from typing import Any
from app.infrastructure.queue.rabbitmq_queue import RabbitMQQueueClient
from app.jobs.email_jobs import PasswordResetEmailJob, PasswordChangedEmailJob
from app.services.email_service import EmailService

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

    async def run(self) -> None:
        self._running = True
        logger.info(
            "Successfully processed email job %s",
            message.payload.get("job_type")
        )

        try:
            while self._running:
                message=await self.queue.dequeue("email.queue")
                if message is None:
                   await asyncio.sleep(1)
                   continue
                try:
                    await self.process_job(message.payload)
                    await message.ack()
                except Exception as exc:
                    logger.exception("Failed to process email job")
                    await message.nack(requeue=True)
        finally:
            await self.queue.close()
               
            
    async def stop(self) -> None:
        self._running = False
        await self.queue.close()

    