from __future__ import annotations

import asyncio
import logging

from app.infrastructure.queue.redis_queue import RedisQueueClient
from app.jobs.email_jobs import PasswordResetEmailJob, PasswordChangedEmailJob
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

EMAIL_QUEUE_NAME = "email_jobs"


class EmailWorker:
    def __init__(self, email_service: EmailService) -> None:
        self.queue = RedisQueueClient()
        self.email_service = email_service
        self._running = False

    async def process_job(self, job_data: dict) -> None:
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
            logger.warning("Unknown job type: %s", job_type)

    async def run(self) -> None:
        self._running = True
        logger.info("Email worker started")

        while self._running:
            try:
                job_data = await self.queue.dequeue(EMAIL_QUEUE_NAME)

                if job_data is not None:
                    try:
                        await self.process_job(job_data)
                    except Exception as exc:
                        logger.exception("Failed to process email job: %s", exc)

                await asyncio.sleep(1)

            except Exception as exc:
                logger.exception("Worker loop error: %s", exc)
                await asyncio.sleep(1)

    async def stop(self) -> None:
        self._running = False
        await self.queue.close()