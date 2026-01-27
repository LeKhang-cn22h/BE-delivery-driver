# presentation/schemas/notification_schema.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class NotificationTypeEnum(str, Enum):
    ORDER = "order"
    DELIVERY = "delivery"
    SYSTEM = "system"
    PROMOTION = "promotion"


class NotificationStatusEnum(str, Enum):
    UNREAD = "unread"
    READ = "read"


class NotificationPriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationCreate(BaseModel):
    """Schema để tạo thông báo"""
    user_id: str = Field(..., description="ID của user")
    title: str = Field(..., min_length=1, max_length=255, description="Tiêu đề thông báo")
    message: str = Field(..., min_length=1, description="Nội dung thông báo")
    type: NotificationTypeEnum = Field(..., description="Loại thông báo")
    priority: NotificationPriorityEnum = Field(
        default=NotificationPriorityEnum.NORMAL,
        description="Mức độ ưu tiên"
    )
    data: Optional[Dict[str, Any]] = Field(None, description="Dữ liệu bổ sung")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Đơn hàng mới",
                "message": "Bạn có đơn hàng mới #12345",
                "type": "order",
                "priority": "high",
                "data": {
                    "order_id": "12345",
                    "total_amount": 500000
                }
            }
        }


class NotificationResponse(BaseModel):
    """Schema response cho thông báo"""
    id: str
    user_id: str
    title: str
    message: str
    type: NotificationTypeEnum
    status: NotificationStatusEnum
    priority: NotificationPriorityEnum
    data: Optional[Dict[str, Any]] = None
    created_at: datetime
    read_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Đơn hàng mới",
                "message": "Bạn có đơn hàng mới #12345",
                "type": "order",
                "status": "unread",
                "priority": "high",
                "data": {"order_id": "12345"},
                "created_at": "2024-01-20T10:30:00Z",
                "read_at": None,
                "deleted_at": None,
                "updated_at": "2024-01-20T10:30:00Z"
            }
        }


class NotificationListResponse(BaseModel):
    """Schema response cho danh sách thông báo"""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int

    class Config:
        json_schema_extra = {
            "example": {
                "notifications": [],
                "total": 50,
                "unread_count": 10,
                "page": 1,
                "page_size": 20
            }
        }


class NotificationUpdate(BaseModel):
    """Schema để cập nhật thông báo"""
    status: Optional[NotificationStatusEnum] = None


class NotificationPreferenceCreate(BaseModel):
    """Schema để tạo preference"""
    user_id: str
    email_enabled: bool = True
    push_enabled: bool = True
    sms_enabled: bool = False
    order_notifications: bool = True
    delivery_notifications: bool = True
    promotion_notifications: bool = True
    system_notifications: bool = True


class NotificationPreferenceUpdate(BaseModel):
    """Schema để cập nhật preference"""
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    order_notifications: Optional[bool] = None
    delivery_notifications: Optional[bool] = None
    promotion_notifications: Optional[bool] = None
    system_notifications: Optional[bool] = None


class NotificationPreferenceResponse(BaseModel):
    """Schema response cho preference"""
    id: str
    user_id: str
    email_enabled: bool
    push_enabled: bool
    sms_enabled: bool
    order_notifications: bool
    delivery_notifications: bool
    promotion_notifications: bool
    system_notifications: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Schema cho error response"""
    detail: str
    status_code: int

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Notification not found",
                "status_code": 404
            }
        }


class SuccessResponse(BaseModel):
    """Schema cho success response"""
    message: str
    data: Optional[Any] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation successful",
                "data": None
            }
        }