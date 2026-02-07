from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.order import Order


class OrderRepository(ABC):
    @abstractmethod
    async def create(self, order: Order) -> Order:
        pass

    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        pass

    @abstractmethod
    async def query_orders(
        self,
        post_office_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        pickup_status: Optional[str] = None,
        order_type: Optional[str] = None,
        pickup_area_code: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> List[Order]:
        """Dynamic query - 1 method thay tất cả get_by_xxx"""
        pass

    @abstractmethod
    async def update_status(self, order_id: str, status: str) -> bool:
        pass

    @abstractmethod
    async def update(self, order: Order) -> Order:
        pass

    # Backward-compatible (xóa dần)
    async def get_by_postid(self, post_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        return await self.query_orders(post_office_id=post_id, skip=skip, limit=limit)

    async def get_by_post_status(self, post_id: str, status: str, skip: int = 0, limit: int = 10) -> List[Order]:
        return await self.query_orders(post_office_id=post_id, status=status, skip=skip, limit=limit)

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        return await self.query_orders(user_id=user_id, skip=skip, limit=limit)

    async def get_by_pickupStatus(self, post_id: str, pickup_status: str, skip: int = 0, limit: int = 10) -> List[Order]:
        return await self.query_orders(post_office_id=post_id, pickup_status=pickup_status, skip=skip, limit=limit)

    async def get_by_pickupStatus_status(self, post_id: str, status: str, pickup_status: str, skip: int = 0, limit: int = 10) -> List[Order]:
        return await self.query_orders(post_office_id=post_id, status=status, pickup_status=pickup_status, skip=skip, limit=limit)