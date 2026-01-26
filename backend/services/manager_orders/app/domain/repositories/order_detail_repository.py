# app/domain/repositories/order_detail_repository.py
from abc import ABC, abstractmethod
from typing import List

from domain.entities.order import OrderDetail


class OrderDetailRepository(ABC):
    @abstractmethod
    async def create_batch(self, order_details: List[OrderDetail]) -> List[OrderDetail]:
        """Tạo nhiều kiện hàng cùng lúc cho 1 đơn"""
        pass

    @abstractmethod
    async def get_by_order_id(self, order_id: str) -> List[OrderDetail]:
        """Lấy tất cả kiện hàng trong đơn"""
        pass

    @abstractmethod
    async def update_detail_status(self, detail_id: str, status: str) -> bool:
        """Cập nhật trạng thái 1 kiện hàng"""
        pass