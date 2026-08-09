import asyncio
import json
from typing import Any

from aio_pika.abc import AbstractIncomingMessage

from app.infrastructure.queue.rabbitmq_queue import RabbitMQQueueClient


MAX_RETRIES = 3


async def handle_test_message(
    queue_client: RabbitMQQueueClient,
    incoming: AbstractIncomingMessage,
) -> None:
    headers = incoming.headers or {}
    retry_count = int(headers.get("x-retry-count", 0))
    payload: dict[str, Any] = json.loads(incoming.body.decode("utf-8"))

    print(f"[consume] payload={payload} retry_count={retry_count}")

    # Intentionally fail only for retry_test
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

    # Non-test messages: ack normally
    await incoming.ack()
    print("[ack] non-test message acked")


async def main() -> None:
    queue_client = RabbitMQQueueClient(
        exchange_name="email.exchange",
        routing_key="email.send",
    )

    try:
        print("Listening on email.queue ... Press Ctrl+C to stop.")
        while True:
            msg = await queue_client.dequeue("email.queue")
            if msg is None:
                await asyncio.sleep(1)
                continue

            # unwrap underlying aio-pika message object
            incoming = msg._message  # matches your RabbitMQMessage wrapper style
            await handle_test_message(queue_client, incoming)
    finally:
        await queue_client.close()


if __name__ == "__main__":
    asyncio.run(main())