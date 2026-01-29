# domain/events/notification_events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
from domain.entities.notification import NotificationType, NotificationPriority


@dataclass
class NotificationEvent:
    """Base Event cho Notification"""
    event_id: str
    timestamp: datetime
    event_type: str


@dataclass
class NotificationCreatedEvent(NotificationEvent):
    """Event khi tạo thông báo mới"""
    notification_id: str
    user_id: str
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value,
            "priority": self.priority.value,
            "data": self.data
        }


@dataclass
class NotificationReadEvent(NotificationEvent):
    """Event khi đọc thông báo"""
    notification_id: str
    user_id: str
    read_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "read_at": self.read_at.isoformat()
        }


@dataclass
class NotificationDeletedEvent(NotificationEvent):
    """Event khi xóa thông báo"""
    notification_id: str
    user_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "notification_id": self.notification_id,
            "user_id": self.user_id
        }


# Events từ các service khác
@dataclass
class OrderCreatedEvent:
    """Event từ Order Service"""
    order_id: str
    user_id: str
    total_amount: float
    items_count: int
    timestamp: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderCreatedEvent':
        return cls(
            order_id=data['order_id'],
            user_id=data['user_id'],
            total_amount=data['total_amount'],
            items_count=data.get('items_count', 0),
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class OrderStatusChangedEvent:
    """Event khi trạng thái đơn hàng thay đổi"""
    order_id: str
    user_id: str
    old_status: str
    new_status: str
    timestamp: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderStatusChangedEvent':
        return cls(
            order_id=data['order_id'],
            user_id=data['user_id'],
            old_status=data['old_status'],
            new_status=data['new_status'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


@dataclass
class DeliveryStatusChangedEvent:
    """Event khi trạng thái giao hàng thay đổi"""
    delivery_id: str
    order_id: str
    user_id: str
    status: str
    location: Optional[str] = None
    timestamp: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeliveryStatusChangedEvent':
        return cls(
            delivery_id=data['delivery_id'],
            order_id=data['order_id'],
            user_id=data['user_id'],
            status=data['status'],
            location=data.get('location'),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.utcnow()
        )