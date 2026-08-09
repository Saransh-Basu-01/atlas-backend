import asyncio

from app.infrastructure.queue.rabbitmq_queue import RabbitMQQueueClient


async def main() -> None:
    queue_client = RabbitMQQueueClient(
        exchange_name="email.exchange",
        routing_key="email.send",
    )

    payload = {
        "job_type": "retry_test",
        "to": "test@example.com",
        "subject": "Retry Flow Test",
        "body": "This message should fail and move to DLQ after retries.",
    }

    try:
        await queue_client.enqueue("email.queue", payload)
        print("Published retry test message to email.queue")
    finally:
        await queue_client.close()


if __name__ == "__main__":
    asyncio.run(main())