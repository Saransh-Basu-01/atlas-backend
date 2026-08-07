import asyncio

from app.infrastructure.queue.rabbitmq_queue import RabbitMQQueueClient


async def main() -> None:
    queue_client = RabbitMQQueueClient(
        exchange_name="email.exchange",
        routing_key="email.send"
    )

    try:
        message = await queue_client.dequeue("email.queue")
        if message is None:
            print("No message Found")
            return 
        print("Recived Payload:",message.payload)
        await message.nack(requeue=True)
        print("Message is nacked")
    finally:
        await queue_client.close()


if __name__ == "__main__":
    asyncio.run(main())