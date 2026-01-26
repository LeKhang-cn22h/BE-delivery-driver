from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class OrderDetailBase(BaseModel):
    """Base model cho Order Detail"""
    order_id: str
    start_point: str
    price: float
    status: str
    address_detail: str
    area_code: str
    location: str
    priority_score: int


class OrderDetail(OrderDetailBase):
    """Order Detail model với ID"""
    id: str


class ScheduleBase(BaseModel):
    """Base model cho Schedule"""
    scheduled_date: datetime
    area_code: str
    status: str = "pending"
    total_orders: int = 0
    completed_orders: int = 0
    failed_orders: int = 0
    post_office_id: str


class Schedule(ScheduleBase):
    """Schedule model với ID"""
    id: str
    created_at: datetime


class ScheduleItemBase(BaseModel):
    """Base model cho Schedule Item"""
    schedule_id: str
    order_detail_id: str
    status: str = "pending"


class ScheduleItem(ScheduleItemBase):
    """Schedule Item model với ID"""
    id: str
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    queue: int


class OrderProcessingResult(BaseModel):
    """Kết quả xử lý đơn hàng"""
    schedule_id: str
    area_code: str
    total_orders: int
    order_detail_ids: List[str]
    created_at: datetime


class BatchProcessingResult(BaseModel):
    """Kết quả xử lý batch đơn hàng"""
    total_schedules: int
    total_orders: int
    schedules: List[OrderProcessingResult]
    processed_at: datetime