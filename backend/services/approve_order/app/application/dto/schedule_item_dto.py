# application/dto/schedule_item_dto.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============================================================================
# REQUEST DTOs
# ============================================================================

class UpdateScheduleItemStatusRequest(BaseModel):
    """Request để cập nhật status của schedule item"""
    status: str = Field(
        ...,
        description="Status mới của item",
        pattern="^(pending|in_progress|completed|failed)$"
    )
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "delivered_at": "2026-01-28T14:30:00",
                "failure_reason": None
            }
        }


class BulkUpdateStatusRequest(BaseModel):
    """Request để cập nhật status nhiều items cùng lúc"""
    item_ids: List[str]
    status: str
    failure_reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "item_ids": ["item-1", "item-2", "item-3"],
                "status": "completed",
                "failure_reason": None
            }
        }


class ReorderItemsRequest(BaseModel):
    """Request để sắp xếp lại thứ tự items"""
    item_orders: List[dict] = Field(
        ...,
        description="Danh sách {item_id: queue_number}"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "item_orders": [
                    {"item_id": "item-1", "queue_number": 1},
                    {"item_id": "item-2", "queue_number": 2},
                    {"item_id": "item-3", "queue_number": 3}
                ]
            }
        }


# ============================================================================
# RESPONSE DTOs
# ============================================================================

class ScheduleItemResponse(BaseModel):
    """Response cơ bản cho schedule item"""
    id: str
    schedule_id: str
    order_detail_id: str
    status: str
    queue_number: int
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "item-123-abc",
                "schedule_id": "sch-123-abc",
                "order_detail_id": "od-123-abc",
                "status": "pending",
                "queue_number": 1,
                "delivered_at": None,
                "failure_reason": None,
                "created_at": "2026-01-27T08:00:00"
            }
        }


class ScheduleItemDetailResponse(ScheduleItemResponse):
    """Response chi tiết bao gồm thông tin order_detail"""
    order_detail: dict  # Thông tin từ order_details

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "item-123",
                "schedule_id": "sch-123",
                "order_detail_id": "od-123",
                "status": "pending",
                "queue_number": 1,
                "order_detail": {
                    "id": "od-123",
                    "address_detail": "123 Nguyễn Huệ, Q1",
                    "area_code": "HCM-Q1",
                    "priority_score": 95,
                    "price": 50000
                }
            }
        }


class ScheduleItemWithOrderInfo(BaseModel):
    """Schedule item kèm thông tin order đầy đủ"""
    id: str
    schedule_id: str
    queue_number: int
    status: str

    # Thông tin order_detail
    order_detail_id: str
    address_detail: str
    area_code: str
    priority_score: int
    price: float
    start_point: str
    location: Optional[dict] = None

    # Tracking info
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    class Config:
        from_attributes = True


class ScheduleItemsListResponse(BaseModel):
    """Response cho danh sách schedule items"""
    schedule_id: str
    total_items: int
    items: List[ScheduleItemWithOrderInfo]

    class Config:
        json_schema_extra = {
            "example": {
                "schedule_id": "sch-123",
                "total_items": 5,
                "items": [
                    {
                        "id": "item-1",
                        "queue_number": 1,
                        "status": "completed",
                        "address_detail": "123 Nguyễn Huệ",
                        "priority_score": 95
                    }
                ]
            }
        }


class ScheduleItemStatusSummary(BaseModel):
    """Tóm tắt status của các items trong schedule"""
    schedule_id: str
    total_items: int
    pending: int
    in_progress: int
    completed: int
    failed: int

    class Config:
        json_schema_extra = {
            "example": {
                "schedule_id": "sch-123",
                "total_items": 10,
                "pending": 3,
                "in_progress": 2,
                "completed": 4,
                "failed": 1
            }
        }


# ============================================================================
# NESTED DTOs (dùng trong responses khác)
# ============================================================================

class ScheduleItemSummary(BaseModel):
    """Thông tin tóm tắt của item (dùng trong list)"""
    id: str
    queue_number: int
    status: str
    address_detail: str
    priority_score: int

    class Config:
        from_attributes = True


class NextDeliveryItem(BaseModel):
    """Item tiếp theo cần giao"""
    item_id: str
    order_detail_id: str
    queue_number: int
    address_detail: str
    area_code: str
    priority_score: int
    location: Optional[dict] = None
    estimated_time: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "item-123",
                "order_detail_id": "od-123",
                "queue_number": 3,
                "address_detail": "123 Nguyễn Huệ, Q1",
                "area_code": "HCM-Q1",
                "priority_score": 95,
                "location": {"latitude": 10.7756, "longitude": 106.6938},
                "estimated_time": "14:30"
            }
        }


class DeliveryRoute(BaseModel):
    """Tuyến đường giao hàng (danh sách items theo thứ tự)"""
    schedule_id: str
    area_code: str
    total_stops: int
    completed_stops: int
    current_stop: Optional[int] = None
    items: List[ScheduleItemSummary]

    class Config:
        json_schema_extra = {
            "example": {
                "schedule_id": "sch-123",
                "area_code": "HCM-Q1",
                "total_stops": 10,
                "completed_stops": 3,
                "current_stop": 4,
                "items": []
            }
        }


class ItemDeliveryHistory(BaseModel):
    """Lịch sử giao hàng của một item"""
    item_id: str
    order_detail_id: str
    status_history: List[dict]  # [{status, timestamp, note}]
    current_status: str

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "item-123",
                "order_detail_id": "od-123",
                "status_history": [
                    {
                        "status": "pending",
                        "timestamp": "2026-01-28T08:00:00",
                        "note": "Created"
                    },
                    {
                        "status": "in_progress",
                        "timestamp": "2026-01-28T10:30:00",
                        "note": "Out for delivery"
                    },
                    {
                        "status": "completed",
                        "timestamp": "2026-01-28T14:30:00",
                        "note": "Delivered successfully"
                    }
                ],
                "current_status": "completed"
            }
        }