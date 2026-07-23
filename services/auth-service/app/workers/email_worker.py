from __future__ import annotations
import asyncio
import json
import logging
from typing import Any
from datetime import datetime, timezone
from app.infrastructure.queue.redis_queue import RedisQueueClient
from app.jobs.email_jobs import PasswordResetEmailJob, PasswordChangedEmailJob
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

EMAIL_QUEUE_NAME = "email_jobs"
EMAIL_PROCESSING_QUEUE = "email_jobs:processing"
EMAIL_DEAD_LETTER_QUEUE = "email_jobs:dead"
MAX_ATTEMPTS = 3
VISIBILITY_TIMEOUT_SECONDS = 60

class EmailWorker:
    def __init__(self, email_service: EmailService) -> None:
        self.queue = RedisQueueClient()
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
        logger.info("Email worker started")

        # Optional: recover jobs left in processing queue after crash

        while self._running:
            try:
                job_data = await self.queue.claim(
                    EMAIL_QUEUE_NAME,
                    EMAIL_PROCESSING_QUEUE,
                    timeout=1,
                )

                if job_data is None:
                    await asyncio.sleep(1)
                    continue

                try:
                    await self.process_job(job_data)
                    await self.queue.ack(EMAIL_PROCESSING_QUEUE,job_data)
                except Exception as exc:
                    logger.exception("Failed to process email job: %s", exc)
                    attempts=int(job_data.get("attempts",0))+1
                    job_data["attempts"]=attempts
                    job_data["last_attempt_at"]=datetime.now(timezone.utc).isoformat()

            except Exception as exc:
                logger.exception("Worker loop error: %s", exc)
                await asyncio.sleep(1)

    