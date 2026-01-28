from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.notification import (
    Notification,
    NotificationType,
    NotificationStatus
)


class NotificationRepository(ABC):
    """Interface cho Notification Repository"""

    @abstractmethod
    async def create(self, notification: Notification) -> Notification:
        """Tạo thông báo mới"""
        pass

    @abstractmethod
    async def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """Lấy thông báo theo ID"""
        pass

    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        type: Optional[NotificationType] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Notification]:
        """Lấy danh sách thông báo của user"""
        pass

    @abstractmethod
    async def update(self, notification: Notification) -> Notification:
        """Cập nhật thông báo"""
        pass

    @abstractmethod
    async def delete(self, notification_id: str) -> bool:
        """Xóa thông báo (soft delete)"""
        pass

    @abstractmethod
    async def mark_as_read(self, notification_id: str) -> bool:
        """Đánh dấu đã đọc"""
        pass

    @abstractmethod
    async def mark_all_as_read(self, user_id: str) -> int:
        """Đánh dấu tất cả đã đọc"""
        pass

    @abstractmethod
    async def get_unread_count(self, user_id: str) -> int:
        """Đếm số thông báo chưa đọc"""
        pass

    @abstractmethod
    async def delete_old_notifications(self, days: int = 30) -> int:
        """Xóa thông báo cũ"""
        pass
