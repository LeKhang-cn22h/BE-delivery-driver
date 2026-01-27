# infrastructure/messaging/kafka_producer.py
from kafka import KafkaProducer
import json
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class NotificationKafkaProducer:
    """Kafka Producer cho Notification Service"""

    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9093"
        )
        self.producer: Optional[KafkaProducer] = None
        self._connect()

    def _connect(self):
        """Kết nối Kafka Producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                max_in_flight_requests_per_connection=1
            )
            logger.info(f"Kafka Producer connected to {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to connect Kafka Producer: {str(e)}")
            self.producer = None

    async def send_notification_created(self, notification_data: Dict[str, Any]) -> bool:
        """Gửi event notification created"""
        return await self._send_event("notification.created", notification_data)

    async def send_notification_read(self, notification_data: Dict[str, Any]) -> bool:
        """Gửi event notification read"""
        return await self._send_event("notification.read", notification_data)

    async def send_notification_deleted(self, notification_data: Dict[str, Any]) -> bool:
        """Gửi event notification deleted"""
        return await self._send_event("notification.deleted", notification_data)

    async def _send_event(self, topic: str, data: Dict[str, Any]) -> bool:
        """Gửi event vào Kafka topic"""
        if not self.producer:
            logger.warning("Kafka Producer not connected. Skipping event send.")
            return False

        try:
            future = self.producer.send(topic, value=data)
            result = future.get(timeout=10)
            logger.info(f"Sent event to {topic}: {data.get('notification_id', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to send event to {topic}: {str(e)}")
            return False

    def close(self):
        """Đóng Kafka Producer"""
        if self.producer:
            self.producer.close()
            logger.info("Kafka Producer closed")