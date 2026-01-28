"""
Schedule Domain
"""
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional
from uuid import UUID


@dataclass
class ScheduleItem:
    """Individual schedule item (order assignment)"""
    id: Optional[UUID] = None
    schedule_id: Optional[UUID] = None
    order_detail_id: UUID = None
    status: str = "pending"  # pending, delivered_at, failure_reason, queue
    delivered_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    queue: Optional[int] = None  # Thứ tự giao hàng trong ca


@dataclass
class Schedule:
    """Schedule aggregate root"""
    id: Optional[UUID] = None
    driver_id: UUID = None
    area_code: str = None
    scheduled_date: datetime = None
    status: str = "pending"  # pending, active, completed
    total_orders: int = 0
    completed_orders: int = 0
    failed_orders: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    post_office_id: Optional[UUID] = None

    # Relationship
    items: List[ScheduleItem] = field(default_factory=list)

    def add_item(self, item: ScheduleItem) -> None:
        """Add order to schedule"""
        self.items.append(item)
        self.total_orders += 1

    def complete_item(self, order_detail_id: UUID) -> None:
        """Mark order as completed"""
        for item in self.items:
            if item.order_detail_id == order_detail_id:
                item.status = "delivered"
                item.delivered_at = datetime.now()
                self.completed_orders += 1
                break

    def fail_item(self, order_detail_id: UUID, reason: str) -> None:
        """Mark order as failed"""
        for item in self.items:
            if item.order_detail_id == order_detail_id:
                item.status = "failed"
                item.failure_reason = reason
                self.failed_orders += 1
                break

    def is_complete(self) -> bool:
        """Check if all orders are processed"""
        return (self.completed_orders + self.failed_orders) == self.total_orders

    def get_completion_rate(self) -> float:
        """Get completion rate percentage"""
        if self.total_orders == 0:
            return 0.0
        return (self.completed_orders / self.total_orders) * 100