from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
from uuid import UUID

class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    processing = "processing"
    completed = "completed"
    cancelled = "cancelled"


class OrderType(str, Enum):
    drop_off = "drop_off"
    pickup = "pickup"


class DetailStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    picking = "picking"
    picked_up = "picked_up"
    delivering = "delivering"
    completed = "completed"
    cancelled = "cancelled"

@dataclass
class OrderDetail:

    id: Optional[str]
    order_id: Optional[str]
    start_point: str  # Địa chỉ giao hàng (người nhận)
    address_detail: str  # Chi tiết địa chỉ giao hàng
    area_code: str  # Mã khu vực giao hàng
    location: Optional[dict]  # Tọa độ địa chỉ giao
    status: DetailStatus  # Trạng thái giao hàng
    priority_score: int  # Độ ưu tiên (cao hơn = giao trước)
    note_send:Optional[str] 
    recipient_id:Optional[str]

    def validate(self):
        if not self.start_point:
            raise ValueError("Địa chỉ giao hàng là bắt buộc")
        if not self.address_detail:
            raise ValueError("Chi tiết địa chỉ là bắt buộc")
        if not self.area_code:
            raise ValueError("Mã khu vực là bắt buộc")


@dataclass
class Order:
    """
    Order = 1 đơn hàng từ khách hàng
    Có thể có nhiều kiện hàng (order_details) giao đến nhiều địa chỉ khác nhau
    """
    id: Optional[str]
    user_id: str  # ID khách hàng đặt hàng
    post_office_id: str
    # Thông tin điểm    lấy hàng (từ khách hàng)
    pickup_point: str  # Địa chỉ lấy hàng
    pickup_address: str  # Chi tiết địa chỉ lấy
    pickup_area_code: str  # Mã khu vực lấy hàng
    pickup_location: Optional[dict]  # Tọa độ điểm lấy
    pickup_phone: str  # SĐT liên hệ lấy hàng
    pickup_note: Optional[str]  # Ghi chú khi lấy hàng

    # Trạng thái và metadata
    status: OrderStatus
    order_type: OrderType
    created_at: Optional[datetime]

    # Danh sách kiện hàng trong đơn
    order_details: List[OrderDetail] = None

    def __post_init__(self):
        if self.order_details is None:
            self.order_details = []

    def validate(self):
        if not self.user_id:
            raise ValueError("User ID là bắt buộc")
        if not self.post_office_id:
            raise ValueError("Bưu cục là bắt buộc")
        if not self.pickup_point:
            raise ValueError("Điểm lấy hàng là bắt buộc")
        if not self.pickup_address:
            raise ValueError("Địa chỉ lấy hàng là bắt buộc")
        if not self.pickup_phone:
            raise ValueError("Số điện thoại là bắt buộc")
        if not self.order_details or len(self.order_details) == 0:
            raise ValueError("Đơn hàng phải có ít nhất 1 kiện hàng")

        # Validate từng kiện hàng
        for detail in self.order_details:
            detail.validate()

    def get_total_packages(self) -> int:
        """Tổng số kiện hàng"""
        return len(self.order_details)

    def get_delivered_packages(self):
        return sum(1 for d in self.order_details if d.status == DetailStatus.completed)

    def get_failed_packages(self):
        return sum(1 for d in self.order_details if d.status == DetailStatus.cancelled)

    def is_all_delivered(self) -> bool:
        return all(d.status == DetailStatus.completed for d in self.order_details)

    def can_cancel(self) -> bool:
        return self.status in [OrderStatus.pending]

    def get_unique_delivery_areas(self) -> List[str]:
        """Lấy danh sách khu vực giao hàng (không trùng)"""
        return list(set(detail.area_code for detail in self.order_details))
