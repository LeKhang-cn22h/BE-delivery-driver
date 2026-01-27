# infrastructure/messaging/kafka_consumer.py
from kafka import KafkaConsumer
import json
import logging
from typing import Callable, Dict, Any, Optional, List
import os
import asyncio

logger = logging.getLogger(__name__)


class NotificationKafkaConsumer:
    """Kafka Consumer cho Notification Service"""

    def __init__(
        self,
        topics: List[str],
        group_id: str = "notification_service_group",
        bootstrap_servers: Optional[str] = None
    ):
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9093"
        )
        self.consumer: Optional[KafkaConsumer] = None
        self.handlers: Dict[str, Callable] = {}
        self.running = False

    def _connect(self):
        """Kết nối Kafka Consumer"""
        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers.split(','),
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                max_poll_records=10
            )
            logger.info(f"Kafka Consumer connected to {self.bootstrap_servers}")
            logger.info(f"Subscribed to topics: {self.topics}")
        except Exception as e:
            logger.error(f"Failed to connect Kafka Consumer: {str(e)}")
            self.consumer = None

    def register_handler(self, topic: str, handler: Callable):
        """Đăng ký handler cho topic"""
        self.handlers[topic] = handler
        logger.info(f"Registered handler for topic: {topic}")

    async def start(self):
        """Bắt đầu consume messages"""
        if not self.consumer:
            self._connect()

        if not self.consumer:
            logger.error("Cannot start consumer - connection failed")
            return

        self.running = True
        logger.info("Starting Kafka Consumer...")

        try:
            for message in self.consumer:
                if not self.running:
                    break

                topic = message.topic
                data = message.value

                logger.info(f"Received message from {topic}: {data}")

                # Gọi handler tương ứng
                handler = self.handlers.get(topic)
                if handler:
                    try:
                        # Nếu handler là async function
                        if asyncio.iscoroutinefunction(handler):
                            await handler(data)
                        else:
                            handler(data)
                    except Exception as e:
                        logger.error(f"Error processing message from {topic}: {str(e)}")
                else:
                    logger.warning(f"No handler registered for topic: {topic}")

        except Exception as e:
            logger.error(f"Error in Kafka Consumer: {str(e)}")
        finally:
            self.stop()

    def stop(self):
        """Dừng consumer"""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka Consumer stopped")

    def close(self):
        """Đóng consumer"""
        self.stop()


# Event Handlers
class NotificationEventHandlers:
    """Handlers cho các event từ Kafka"""

    def __init__(self, notification_service):
        self.notification_service = notification_service

    async def handle_order_created(self, data: Dict[str, Any]):
        """Xử lý event order created"""
        try:
            logger.info(f"Processing order.created event: {data}")
            
            # Tạo thông báo cho user
            await self.notification_service.create_order_notification(
                user_id=data['user_id'],
                order_id=data['order_id'],
                total_amount=data.get('total_amount', 0),
                items_count=data.get('items_count', 0)
            )
        except Exception as e:
            logger.error(f"Error handling order.created: {str(e)}")

    async def handle_order_status_changed(self, data: Dict[str, Any]):
        """Xử lý event order status changed"""
        try:
            logger.info(f"Processing order.status_changed event: {data}")
            
            await self.notification_service.create_order_status_notification(
                user_id=data['user_id'],
                order_id=data['order_id'],
                old_status=data['old_status'],
                new_status=data['new_status']
            )
        except Exception as e:
            logger.error(f"Error handling order.status_changed: {str(e)}")

    async def handle_delivery_status_changed(self, data: Dict[str, Any]):
        """Xử lý event delivery status changed"""
        try:
            logger.info(f"Processing delivery.status_changed event: {data}")
            
            await self.notification_service.create_delivery_notification(
                user_id=data['user_id'],
                order_id=data['order_id'],
                delivery_id=data['delivery_id'],
                status=data['status'],
                location=data.get('location')
            )
        except Exception as e:
            logger.error(f"Error handling delivery.status_changed: {str(e)}")