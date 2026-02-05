# domain/events/base_event.py
from datetime import datetime
from typing import Dict, Any


class DomainEvent:
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload
        self.occurred_at = datetime.utcnow()

    @property
    def event_name(self) -> str:
        return self.__class__.__name__

    def to_dict(self):
        return {
            "event_name": self.event_name,
            "occurred_at": self.occurred_at.isoformat(),
            "payload": self.payload
        }
