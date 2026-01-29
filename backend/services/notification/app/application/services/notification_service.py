# application/services/notification_service.py
from typing import Dict, Any, Optional
import logging

from domain.entities.notification import (
    Notification,
    NotificationType,
    NotificationPriority
)
from domain.repositories.notification_repository import NotificationRepository
from infrastructure.messaging.kafka_producer import NotificationKafkaProducer

logger = logging.getLogger(__name__)


class NotificationService:
    """Service xử lý business logic cho Notification"""

    def __init__(
        self,
        repository: NotificationRepository,
        kafka_producer: Optional[NotificationKafkaProducer] = None
    ):
        self.repository = repository
        self.kafka_producer = kafka_producer

    async def create_order_notification(
        self,
        user_id: str,
        order_id: str,
        total_amount: float,
        items_count: int
    ) -> Notification:
        """Tạo thông báo khi có đơn hàng mới"""
        notification = Notification(
            user_id=user_id,
            title="Đơn hàng mới",
            message=f"Bạn có đơn hàng mới #{order_id} với {items_count} sản phẩm, tổng giá trị {total_amount:,.0f} VND",
            type=NotificationType.ORDER,
            priority=NotificationPriority.HIGH,
            data={
                "order_id": order_id,
                "total_amount": total_amount,
                "items_count": items_count
            }
        )
        
        result = await self.repository.create(notification)
        
        # Publish event
        if self.kafka_producer:
            await self.kafka_producer.send_notification_created({
                "notification_id": result.id,
                "user_id": result.user_id,
                "type": result.type.value,
                "title": result.title
            })
        
        return result

    async def create_order_status_notification(
        self,
        user_id: str,
        order_id: str,
        old_status: str,
        new_status: str
    ) -> Notification:
        """Tạo thông báo khi trạng thái đơn hàng thay đổi"""
        status_messages = {
            "confirmed": "Đơn hàng đã được xác nhận",
            "processing": "Đơn hàng đang được xử lý",
            "shipped": "Đơn hàng đã được giao cho đơn vị vận chuyển",
            "delivered": "Đơn hàng đã được giao thành công",
            "cancelled": "Đơn hàng đã bị hủy"
        }
        
        message = status_messages.get(new_status, f"Trạng thái đơn hàng đã thay đổi thành {new_status}")
        
        notification = Notification(
            user_id=user_id,
            title=f"Cập nhật đơn hàng #{order_id}",
            message=message,
            type=NotificationType.ORDER,
            priority=NotificationPriority.NORMAL,
            data={
                "order_id": order_id,
                "old_status": old_status,
                "new_status": new_status
            }
        )
        
        result = await self.repository.create(notification)
        
        if self.kafka_producer:
            await self.kafka_producer.send_notification_created({
                "notification_id": result.id,
                "user_id": result.user_id,
                "type": result.type.value,
                "title": result.title
            })
        
        return result

    async def create_delivery_notification(
        self,
        user_id: str,
        order_id: str,
        delivery_id: str,
        status: str,
        location: Optional[str] = None
    ) -> Notification:
        """Tạo thông báo về trạng thái giao hàng"""
        status_messages = {
            "picked_up": "Đơn hàng đã được lấy",
            "in_transit": "Đơn hàng đang trên đường giao",
            "out_for_delivery": "Đơn hàng đang được giao đến bạn",
            "delivered": "Đơn hàng đã được giao thành công",
            "failed": "Giao hàng không thành công"
        }
        
        message = status_messages.get(status, f"Trạng thái giao hàng: {status}")
        if location:
            message += f" tại {location}"
        
        notification = Notification(
            user_id=user_id,
            title=f"Cập nhật giao hàng #{order_id}",
            message=message,
            type=NotificationType.DELIVERY,
            priority=NotificationPriority.NORMAL if status != "delivered" else NotificationPriority.HIGH,
            data={
                "order_id": order_id,
                "delivery_id": delivery_id,
                "status": status,
                "location": location
            }
        )
        
        result = await self.repository.create(notification)
        
        if self.kafka_producer:
            await self.kafka_producer.send_notification_created({
                "notification_id": result.id,
                "user_id": result.user_id,
                "type": result.type.value,
                "title": result.title
            })
        
        return result

    async def create_system_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Tạo thông báo hệ thống"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=NotificationType.SYSTEM,
            priority=priority,
            data=data
        )
        
        result = await self.repository.create(notification)
        
        if self.kafka_producer:
            await self.kafka_producer.send_notification_created({
                "notification_id": result.id,
                "user_id": result.user_id,
                "type": result.type.value,
                "title": result.title
            })
        
        return result

    async def create_promotion_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """Tạo thông báo khuyến mãi"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=NotificationType.PROMOTION,
            priority=NotificationPriority.LOW,
            data=data
        )
        
        result = await self.repository.create(notification)
        
        if self.kafka_producer:
            await self.kafka_producer.send_notification_created({
                "notification_id": result.id,
                "user_id": result.user_id,
                "type": result.type.value,
                "title": result.title
            })
        
        return result