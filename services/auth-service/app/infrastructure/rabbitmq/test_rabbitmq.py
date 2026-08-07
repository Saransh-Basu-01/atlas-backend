import asyncio

from app.infrastructure.queue.rabbitmq_queue import RabbitMQQueueClient


async def main() -> None:
    client = RabbitMQQueueClient( 
        exchange_name="email.exchange",
        routing_key="email.send"
        )

    payload = {
        "job_type": "test_email",
        "message": "RabbitMQ is working",
    }

    try:
        await client.enqueue("email.queue", payload)
        print("Message published successfully.")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())