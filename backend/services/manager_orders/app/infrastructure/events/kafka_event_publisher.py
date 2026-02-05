#services/manager_order/app/infrastructure/events/kafka_event_publisher.py
import json
import logging
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from domain.events.event_publisher import EventPublisher
from domain.events.base_event import DomainEvent

logger = logging.getLogger(__name__)


class KafkaEventPublisher(EventPublisher):
    """
    Kafka Event Publisher with Graceful Degradation
    If Kafka is unavailable, logs events instead of crashing
    """

    def __init__(self, bootstrap_servers: str = "kafka:9093"):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self._started = False
        logger.info(f"KafkaEventPublisher initialized with: {bootstrap_servers}")

    async def start(self):
        """Start Kafka producer - Returns success status"""
        if self._started:
            logger.warning("Producer already started")
            return True

        try:
            logger.info(f"Starting Kafka producer: {self.bootstrap_servers}")

            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                acks='all',
                request_timeout_ms=30000,
                compression_type='gzip'
            )

            await self.producer.start()
            self._started = True

            logger.info(f"✅ Kafka Producer started successfully: {self.bootstrap_servers}")
            return True

        except KafkaError as e:
            logger.error(f"❌ Failed to start Kafka Producer: {e}")
            logger.warning("⚠️ Events will be logged instead of published to Kafka")
            self._started = False
            return False

        except Exception as e:
            logger.error(f"❌ Unexpected error starting Kafka Producer: {e}")
            logger.exception(e)
            self._started = False
            return False

    async def stop(self):
        """Stop Kafka producer"""
        if self.producer and self._started:
            try:
                logger.info("Stopping Kafka producer...")
                await self.producer.stop()
                self._started = False
                logger.info("✅ Kafka Producer stopped")
            except Exception as e:
                logger.error(f"❌ Error stopping producer: {e}")

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish event to Kafka or log if unavailable

        Args:
            event: Domain event to publish
        """
        event_dict = event.to_dict()

        # If Kafka is not available, log event instead
        if not self._started or not self.producer:
            logger.warning(
                f"⚠️ Kafka not available - Event logged instead | "
                f"event={event.event_name} | "
                f"payload={json.dumps(event_dict)}"
            )
            return

        try:
            logger.info(f"📤 Publishing event: {event.event_name}")
            logger.debug(f"Event data: {json.dumps(event_dict, indent=2)}")

            # Send to Kafka
            record_metadata = await self.producer.send_and_wait(
                topic="orders",
                value=event_dict
            )

            logger.info(
                f"✅ Event published successfully | "
                f"event={event.event_name} | "
                f"topic={record_metadata.topic} | "
                f"partition={record_metadata.partition} | "
                f"offset={record_metadata.offset}"
            )

        except Exception as e:
            # Log error but don't crash the application
            logger.error(f"❌ Failed to publish event {event.event_name}: {e}")
            logger.warning(f"⚠️ Event data: {json.dumps(event_dict)}")
            # Don't raise - allow application to continue