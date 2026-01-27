"""

"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class Driver:

    id: UUID
    user_id: UUID
    name: str
    phone: str
    status: str  # active, inactive, busy
    created_at: datetime
    post_office_id: UUID

    # Additional computed fields
    current_orders: int = 0
    area_expertise: Optional[str] = None  # Khu vực tài xế quen thuộc

    def is_available(self) -> bool:
        """Check if driver is available for scheduling"""
        return self.status == "active"

    def can_take_more_orders(self, max_orders: int) -> bool:
        """Check if driver can take more orders"""
        return self.current_orders < max_orders

    def assign_orders(self, count: int) -> None:
        """Assign orders to driver"""
        self.current_orders += count
        if self.current_orders > 0:
            self.status = "busy"