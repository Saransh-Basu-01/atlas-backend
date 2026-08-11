import asyncio
from app.services.email_service import EmailService
from app.workers.email_worker_rabbitmq import RabbitMQEmailWorker

async def main():
    worker = RabbitMQEmailWorker(email_service=EmailService())
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())