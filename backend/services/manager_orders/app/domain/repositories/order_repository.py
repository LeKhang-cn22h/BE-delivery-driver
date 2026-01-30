
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
    async def get_by_postid(self, post_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy danh sách đơn hàng của cửa hàng"""
        pass

    @abstractmethod
    async def get_by_post_status(self, post_id: str, status:str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy danh sách đơn hàng của cửa hàng theo trạng thái"""
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy danh sách đơn hàng của khách hàng"""
        pass
        
    @abstractmethod
    async def get_by_pickupStatus(self, post_id: str,pickup_status:str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy danh sách đơn hàng theo cử hàng và pickup status"""
        pass

    @abstractmethod
    async def get_by_pickupStatus_status(self, post_id: str,status:str,pickup_status:str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy danh sách đơn hàng theo cử hàng và pickupstatus và status"""
        pass

    @abstractmethod
    async def update_status(self, order_id: str, status: str) -> bool:
        """Cập nhật trạng thái đơn hàng"""
        pass

    @abstractmethod
    async def update(self, order: Order) -> Order:
        """Cập nhật toàn bộ thông tin đơn hàng"""
        pass
