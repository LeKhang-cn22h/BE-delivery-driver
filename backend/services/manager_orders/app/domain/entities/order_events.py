from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from domain.entities.order import OrderType


@dataclass
class OrderCreatedEvent:
    """Event được publish khi đơn hàng được tạo"""
    order_id: str
    customer_id: str
    order_type: OrderType
    timestamp: datetime
    total_details: int

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "order_type": self.order_type.value,
            "timestamp": self.timestamp.isoformat(),
            "total_details": self.total_details
        }
    