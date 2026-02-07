"""
Order Domain
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class OrderDetail:
    """Order detailfor scheduling"""
    id: UUID
    order_id: UUID
    start_point: str  # JSON text hoặc địa chỉ
    status: str
    address_detail: Optional[str] = None
    area_code: str = None
    location: Optional[str] = None  # PostGIS point
    priority_score: Optional[int] = None
    pickup_area_code: Optional[str] = None
    pickup_location: Optional[str] = None  # PostGIS point

    # Related order info
    pickup_point: Optional[str] = None
    order_type: Optional[str] = None  # normal, express, fragile
    created_at: Optional[datetime] = None

    def get_priority(self) -> int:
        """Get order priority (higher is more important)"""
        if self.priority_score:
            return self.priority_score

        # Default priority based on order type
        priority_map = {
            "express": 100,
            "fragile": 80,
            "normal": 50
        }
        return priority_map.get(self.order_type, 50)

    def is_same_area(self, area_code: str) -> bool:
        """Check if order is in the same area"""
        return self.area_code == area_code


@dataclass
class Order:
    """Order aggregate"""
    id: UUID
    user_id: UUID
    pickup_point:Optional[str] = None
    status: str
    created_at: datetime
    order_type: str = "normal"
    pickup_address: Optional[str] = None
    pickup_area_code: Optional[str] = None
    pickup_phone: Optional[str] = None
    pickup_note: Optional[str] = None
    pickup_status: Optional[str] = None
    pickup_driver_id: Optional[UUID] = None
    pickup_failure_reason: Optional[str] = None
    post_office_id: Optional[UUID] = None