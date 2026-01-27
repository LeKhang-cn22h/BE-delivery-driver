from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OrderDetail(BaseModel):
    id: str
    order_id: str
    start_point: str
    price: float
    status: str
    address_detail: Optional[str] = None
    area_code: Optional[str] = None
    location: Optional[dict] = None
    priority_score: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Schedule(BaseModel):
    id: str
    post_office_id: str
    area_code: str
    scheduled_date: datetime
    status: str
    total_orders: int
    completed_orders: int = 0
    failed_orders: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleItem(BaseModel):
    id: str
    schedule_id: str
    order_detail_id: str
    status: str
    queue: int
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True