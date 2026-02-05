#infrastructure/events/simple_event_publisher.py
import logging
from domain.events.event_publisher import EventPublisher
from domain.events.base_event import DomainEvent


logger = logging.getLogger(__name__)


class SimpleEventPublisher(EventPublisher):
    async def publish(self, event: DomainEvent) -> None:
        # Tạm thời chỉ log ra console
        logger.info(
            "[EVENT] %s | payload=%s",
            event.event_name,
            event.payload
        )
