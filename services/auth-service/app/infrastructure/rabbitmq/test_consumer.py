import asyncio

from app.infrastructure.queue.rabbitmq_queue import RabbitMQQueueClient


async def main() -> None:
    queue_client = RabbitMQQueueClient()

    try:
        message = await queue_client.dequeue("email.queue")
        print(message)
    finally:
        await queue_client.close()


if __name__ == "__main__":
    asyncio.run(main())