# application/dto/schedule_item_dto.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UpdateScheduleItemStatusRequest(BaseModel):
    """Request để cập nhật status của schedule item"""
    status: str 
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

class BulkUpdateStatusRequest(BaseModel):
    """Request để cập nhật status nhiều items cùng lúc"""
    item_ids: List[str]
    status: str
    failure_reason: Optional[str] = None

class ReorderItemsRequest(BaseModel):
    """Request để sắp xếp lại thứ tự items"""
    item_orders: List[dict] = Field(
        ...,
        description="Danh sách {item_id: queue_number}"
    )

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

class ScheduleItemDetailResponse(ScheduleItemResponse):
    """Response chi tiết bao gồm thông tin order_detail"""
    order_detail: dict  # Thông tin từ order_details


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

class ScheduleItemStatusSummary(BaseModel):
    """Tóm tắt status của các items trong schedule"""
    schedule_id: str
    total_items: int
    pending: int
    in_progress: int
    completed: int
    failed: int

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


class DeliveryRoute(BaseModel):
    """Tuyến đường giao hàng (danh sách items theo thứ tự)"""
    schedule_id: str
    area_code: str
    total_stops: int
    completed_stops: int
    current_stop: Optional[int] = None
    items: List[ScheduleItemSummary]


class ItemDeliveryHistory(BaseModel):
    """Lịch sử giao hàng của một item"""
    item_id: str
    order_detail_id: str
    status_history: List[dict]  # [{status, timestamp, note}]
    current_status: str
