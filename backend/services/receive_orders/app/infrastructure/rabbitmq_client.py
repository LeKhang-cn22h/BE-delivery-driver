import os
import asyncio
import json
from aio_pika import connect_robust, Message, ExchangeType
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
import logging

logger = logging.getLogger(__name__)


class RabbitMQClient:
    def __init__(self):
        self.connection: AbstractConnection = None
        self.channel: AbstractChannel = None
        self.queue: AbstractQueue = None
        self.exchange = None

        self.host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        self.port = int(os.getenv("RABBITMQ_PORT", 5672))
        self.user = os.getenv("RABBITMQ_USER", "guest")
        self.password = os.getenv("RABBITMQ_PASSWORD", "guest")
        self.queue_name = os.getenv("RABBITMQ_QUEUE_NAME", "order_queue")
        self.exchange_name = os.getenv("RABBITMQ_EXCHANGE_NAME", "orders_exchange")
        self.routing_key = os.getenv("RABBITMQ_ROUTING_KEY", "new.order")

    async def connect(self):
        """Kết nối tới RabbitMQ"""
        try:
            connection_url = f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"
            self.connection = await connect_robust(connection_url)
            self.channel = await self.connection.channel()

            # Tạo exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                ExchangeType.TOPIC,
                durable=True
            )

            # Tạo queue
            self.queue = await self.channel.declare_queue(
                self.queue_name,
                durable=True
            )

            # Bind queue với exchange
            await self.queue.bind(self.exchange, routing_key=self.routing_key)

            logger.info(f"✅ Connected to RabbitMQ: {self.host}:{self.port}")
            logger.info(f"📬 Queue: {self.queue_name}")
            logger.info(f"🔀 Exchange: {self.exchange_name}")

        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """Ngắt kết nối"""
        if self.connection:
            await self.connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def consume(self, callback):
        """Lắng nghe và xử lý messages"""
        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        data = json.loads(message.body.decode())
                        logger.info(f"📨 Received message: {data}")
                        await callback(data)
                    except Exception as e:
                        logger.error(f"❌ Error processing message: {e}")

    async def publish(self, message_data: dict, routing_key: str = None):
        """Gửi message (nếu cần publish ngược lại)"""
        try:
            key = routing_key or self.routing_key
            message = Message(
                json.dumps(message_data).encode(),
                content_type="application/json",
                delivery_mode=2  # persistent
            )
            await self.exchange.publish(message, routing_key=key)
            logger.info(f"✉️ Published message to {key}")
        except Exception as e:
            logger.error(f"❌ Failed to publish message: {e}")
            raise