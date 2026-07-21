from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.infrastructure.queue.redis_queue import RedisQueueClient
from app.jobs.email_jobs import PasswordResetEmailJob, PasswordChangedEmailJob
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

EMAIL_QUEUE_NAME = "email_jobs"
EMAIL_PROCESSING_QUEUE = "email_jobs:processing"
EMAIL_DEAD_LETTER_QUEUE = "email_jobs:dead"
MAX_ATTEMPTS = 3


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
        await self._recover_processing_jobs()

        while self._running:
            try:
                result = await self.queue._client.brpoplpush(
                    EMAIL_QUEUE_NAME,
                    EMAIL_PROCESSING_QUEUE,
                    timeout=1,
                )

                if result is None:
                    continue

                raw_job = result
                job_data = json.loads(raw_job)

                try:
                    await self.process_job(job_data)
                    await self._acknowledge_job(raw_job)
                except Exception as exc:
                    logger.exception("Failed to process email job: %s", exc)
                    await self._handle_failed_job(raw_job, job_data)

            except Exception as exc:
                logger.exception("Worker loop error: %s", exc)
                await asyncio.sleep(1)

    async def stop(self) -> None:
        self._running = False
        await self.queue.close()

    async def _acknowledge_job(self, raw_job: str) -> None:
        await self.queue._client.lrem(EMAIL_PROCESSING_QUEUE, 0, raw_job)

    async def _handle_failed_job(self, raw_job: str, job_data: dict[str, Any]) -> None:
        attempts = int(job_data.get("attempts", 0)) + 1
        job_data["attempts"] = attempts

        await self.queue._client.lrem(EMAIL_PROCESSING_QUEUE, 0, raw_job)

        if attempts >= MAX_ATTEMPTS:
            await self.queue._client.lpush(
                EMAIL_DEAD_LETTER_QUEUE,
                json.dumps(job_data),
            )
            logger.error("Moved job to dead-letter queue: %s", job_data)
        else:
            await self.queue._client.lpush(
                EMAIL_QUEUE_NAME,
                json.dumps(job_data),
            )
            logger.warning("Requeued job for retry (%s/%s)", attempts, MAX_ATTEMPTS)

    async def _recover_processing_jobs(self) -> None:
        """
        Move any leftover jobs from processing back to main queue on startup.
        This is a simple crash-recovery strategy.
        """
        while True:
            raw_job = await self.queue._client.rpop(EMAIL_PROCESSING_QUEUE)
            if raw_job is None:
                break
            await self.queue._client.lpush(EMAIL_QUEUE_NAME, raw_job)