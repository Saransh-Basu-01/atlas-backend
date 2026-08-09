import asyncio
import json
from typing import Any

from aio_pika.abc import AbstractIncomingMessage

from app.infrastructure.queue.rabbitmq_queue import RabbitMQQueueClient

MAX_RETRIES = 3


async def main() -> None:
    queue_client = RabbitMQQueueClient(
        exchange_name="email.exchange",
        routing_key="email.send",
    )

    async def callback(incoming: AbstractIncomingMessage) -> None:
        payload: dict[str, Any] = json.loads(incoming.body.decode("utf-8"))
        retry_count = queue_client.get_retry_count(incoming)

        print(f"[consume] payload={payload} retry_count={retry_count}")

        if payload.get("job_type") == "retry_test":
            print("[fail] Testing RabbitMQ retry")
            was_retried = await queue_client.retry_message(
                incoming,
                max_retries=MAX_RETRIES,
            )
            if was_retried:
                print(f"[retry] republished with x-retry-count={retry_count + 1}")
            else:
                print("[dlq] max retries exceeded, moving to email.dead.queue")
                await queue_client.move_to_dead_queue(
                    message=incoming,
                    dead_queue_name="email.dead.queue",
                    payload=payload,
                )
            return

        await incoming.ack()
        print("[ack] non-test message acked")

    try:
        print("Listening on email.queue ... Press Ctrl+C to stop.")
        await queue_client.consume("email.queue", callback)
        await asyncio.Future()  # keep running
    finally:
        await queue_client.close()


if __name__ == "__main__":
    asyncio.run(main())