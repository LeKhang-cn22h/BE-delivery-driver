# application/use_cases/notification_use_cases.py

from typing import List, Optional, Dict, Any
import logging
import os
import httpx

from domain.entities.notification import (
    Notification,
    NotificationType,
    NotificationStatus,
    NotificationPriority
)
from domain.repositories.notification_repository import NotificationRepository


logger = logging.getLogger(__name__)


class CreateNotificationUseCase:
    """Use case: Tạo thông báo mới"""

    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    async def execute(
        self,
        user_id: str,
        title: str,
        message: str,
        type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Tạo thông báo"""
        try:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                type=type,
                priority=priority,
                data=data
            )
            
            result = await self.repository.create(notification)
            logger.info(f"Created notification {result.id} for user {user_id}")
            return result
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise


class GetNotificationsUseCase:
    """Use case: Lấy danh sách thông báo"""

    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    async def execute(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        type: Optional[NotificationType] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Notification]:
        """Lấy danh sách thông báo của user"""
        try:
            notifications = await self.repository.get_by_user_id(
                user_id=user_id,
                status=status,
                type=type,
                limit=limit,
                offset=offset
            )
            logger.info(f"Retrieved {len(notifications)} notifications for user {user_id}")
            return notifications
        except Exception as e:
            logger.error(f"Error getting notifications: {str(e)}")
            raise


class GetNotificationByIdUseCase:
    """Use case: Lấy thông báo theo ID"""

    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    async def execute(self, notification_id: str) -> Optional[Notification]:
        """Lấy thông báo theo ID"""
        try:
            notification = await self.repository.get_by_id(notification_id)
            if notification:
                logger.info(f"Retrieved notification {notification_id}")
            return notification
        except Exception as e:
            logger.error(f"Error getting notification {notification_id}: {str(e)}")
            raise


class MarkAsReadUseCase:
    """Use case: Đánh dấu đã đọc"""

    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    async def execute(self, notification_id: str) -> bool:
        """Đánh dấu thông báo đã đọc"""
        try:
            result = await self.repository.mark_as_read(notification_id)
            if result:
                logger.info(f"Marked notification {notification_id} as read")
            return result
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            raise


class MarkAllAsReadUseCase:
    """Use case: Đánh dấu tất cả đã đọc"""

    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    async def execute(self, user_id: str) -> int:
        """Đánh dấu tất cả thông báo của user đã đọc"""
        try:
            count = await self.repository.mark_all_as_read(user_id)
            logger.info(f"Marked {count} notifications as read for user {user_id}")
            return count
        except Exception as e:
            logger.error(f"Error marking all as read: {str(e)}")
            raise


class DeleteNotificationUseCase:
    """Use case: Xóa thông báo"""

    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    async def execute(self, notification_id: str) -> bool:
        """Xóa thông báo"""
        try:
            result = await self.repository.delete(notification_id)
            if result:
                logger.info(f"Deleted notification {notification_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting notification: {str(e)}")
            raise


class GetUnreadCountUseCase:
    """Use case: Đếm số thông báo chưa đọc"""

    def __init__(self, repository: NotificationRepository):
        self.repository = repository

    async def execute(self, user_id: str) -> int:
        """Đếm số thông báo chưa đọc của user"""
        try:
            count = await self.repository.get_unread_count(user_id)
            logger.info(f"User {user_id} has {count} unread notifications")
            return count
        except Exception as e:
            logger.error(f"Error getting unread count: {str(e)}")
            raise


class SendMultiChannelNotificationUseCase:
    """
    Use case: Gửi thông báo qua nhiều kênh (Microservice version)
    """

    def __init__(self, repository: NotificationRepository):
        self.repository = repository
        self.email_service_url = os.getenv("EMAIL_SERVICE_URL", "http://localhost:8010")
        self.push_service_url = os.getenv("PUSH_NOTIFICATION_SERVICE_URL", "http://localhost:8011")
        
        logger.info(f"Email Service URL: {self.email_service_url}")
        logger.info(f"Push Service URL: {self.push_service_url}")

    async def execute(
        self,
        user_id: str,
        user_type: str,  # "customer" hoặc "shipper"
        title: str,
        body: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        user_email: Optional[str] = None,
        device_token: Optional[str] = None,
        html_body: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Gửi thông báo qua multiple channels (Microservice)."""
        try:
            logger.info(f"Sending {notification_type} notification to {user_type} {user_id}")

            # Step 1: Tạo thông báo vào Supabase
            notification = Notification(
                user_id=user_id,
                title=title,
                message=body,
                type=notification_type,
                priority=priority,
                data=data or {},
            )
            
            db_notification = await self.repository.create(notification)
            logger.info(f"Notification saved to DB: {db_notification.id}")

            # Step 2: Gửi tới external services
            if user_type == "customer":
                await self._send_email_via_service(user_id, user_email, title, body, html_body)
            elif user_type == "shipper":
                await self._send_push_via_service(user_id, device_token, title, body, data)
            else:
                logger.warning(f"Unknown user type: {user_type}")

            return db_notification

        except Exception as e:
            logger.error(f"Error sending multi-channel notification: {str(e)}")
            raise

    async def _send_email_via_service(
        self, user_id: str, user_email: str, title: str, body: str, html_body: Optional[str]
    ) -> bool:
        """Call Email Service (Port 8010) via HTTP POST."""
        try:
            if not user_email:
                logger.warning(f"User {user_id} has no email")
                return False

            payload = {
                "user_id": user_id,
                "to_email": user_email,
                "subject": title,
                "body": body,
            }
            if html_body:
                payload["html_body"] = html_body

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.email_service_url}/send", json=payload)
                
                if response.status_code == 200:
                    logger.info(f"Email sent to {user_email} (via Email Service)")
                    return True
                else:
                    logger.warning(f"Email Service returned {response.status_code}")
                    return False

        except httpx.ConnectError:
            logger.error(f"Cannot connect to Email Service: {self.email_service_url}")
            return False
        except Exception as e:
            logger.error(f"Error calling Email Service: {str(e)}")
            return False

    async def _send_push_via_service(
        self, user_id: str, device_token: str, title: str, body: str, data: Optional[Dict[str, Any]]
    ) -> bool:
        """Call Push Service (Port 8011) via HTTP POST."""
        try:
            if not device_token:
                logger.warning(f"User {user_id} has no device token")
                return False

            payload = {
                "user_id": user_id,
                "device_token": device_token,
                "title": title,
                "body": body,
                "data": data or {"user_id": user_id},
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.push_service_url}/send", json=payload)
                
                if response.status_code == 200:
                    logger.info(f"Push sent to device {device_token[:20]}... (via Push Service)")
                    return True
                else:
                    logger.warning(f"Push Service returned {response.status_code}")
                    return False

        except httpx.ConnectError:
            logger.error(f"Cannot connect to Push Service: {self.push_service_url}")
            return False
        except Exception as e:
            logger.error(f"Error calling Push Service: {str(e)}")
            return False
