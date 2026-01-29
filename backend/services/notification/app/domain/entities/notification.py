# domain/entities/notification.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class NotificationType(str, Enum):
    """Loại thông báo"""
    ORDER = "order"
    DELIVERY = "delivery"
    SYSTEM = "system"
    PROMOTION = "promotion"


class NotificationStatus(str, Enum):
    """Trạng thái thông báo"""
    UNREAD = "unread"
    READ = "read"


class NotificationPriority(str, Enum):
    """Mức độ ưu tiên"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """Entity Notification"""
    user_id: str
    title: str
    message: str
    type: NotificationType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: NotificationStatus = NotificationStatus.UNREAD
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_as_read(self) -> None:
        """Đánh dấu đã đọc"""
        if self.status == NotificationStatus.UNREAD:
            self.status = NotificationStatus.READ
            self.read_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """Xóa mềm thông báo"""
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def is_deleted(self) -> bool:
        """Kiểm tra đã xóa chưa"""
        return self.deleted_at is not None

    def is_read(self) -> bool:
        """Kiểm tra đã đọc chưa"""
        return self.status == NotificationStatus.READ

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value,
            "status": self.status.value,
            "priority": self.priority.value,
            "data": self.data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class NotificationPreference:
    """Entity Notification Preference"""
    user_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    order_notifications: bool = True
    delivery_notifications: bool = True
    promotion_notifications: bool = True
    system_notifications: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update(self, **kwargs) -> None:
        """Cập nhật preference"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()

    def is_notification_enabled(self, notification_type: NotificationType) -> bool:
        """Kiểm tra loại thông báo có được bật không"""
        type_mapping = {
            NotificationType.ORDER: self.order_notifications,
            NotificationType.DELIVERY: self.delivery_notifications,
            NotificationType.PROMOTION: self.promotion_notifications,
            NotificationType.SYSTEM: self.system_notifications,
        }
        return type_mapping.get(notification_type, True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email_enabled": self.email_enabled,
            "push_enabled": self.push_enabled,
            "sms_enabled": self.sms_enabled,
            "order_notifications": self.order_notifications,
            "delivery_notifications": self.delivery_notifications,
            "promotion_notifications": self.promotion_notifications,
            "system_notifications": self.system_notifications,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }