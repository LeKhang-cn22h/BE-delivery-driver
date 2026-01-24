# app/domain/repositories/order_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.order import Order


class OrderRepository(ABC):
    @abstractmethod
    async def create(self, order: Order) -> Order:
        """Tạo đơn hàng mới"""
        pass

    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        """Lấy đơn hàng theo ID"""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy danh sách đơn hàng của khách hàng"""
        pass

    @abstractmethod
    async def update_status(self, order_id: str, status: str) -> bool:
        """Cập nhật trạng thái đơn hàng"""
        pass

    @abstractmethod
    async def update(self, order: Order) -> Order:
        """Cập nhật toàn bộ thông tin đơn hàng"""
        pass
