from typing import List, Optional

from domain.entities.order import Order
from domain.repositories.order_repository import OrderRepository


class GetOrderUseCase:
    def __init__(self, order_repository: OrderRepository,detail_repository=None):
        self.order_repository = order_repository
        self.detail_repository = detail_repository
    async def execute(self, order_id: str) -> Optional[Order]:
        # Chuẩn Clean Architecture: router chỉ gọi execute
        return await self.get_by_id(order_id)
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError(f"Không tìm thấy đơn hàng: {order_id}")
        return order

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
        """
        Unified query - pass through tất cả filters xuống repository.
        """
        return await self.order_repository.query_orders(
            post_office_id=post_office_id,
            user_id=user_id,
            status=status,
            pickup_status=pickup_status,
            order_type=order_type,
            pickup_area_code=pickup_area_code,
            skip=skip,
            limit=limit,
        )

    # Backward-compatible (xóa dần)
    async def getbyPost(self, post_id, skip=0, limit=10):
        return await self.query_orders(post_office_id=post_id, skip=skip, limit=limit)

    async def getbyStatus(self, post_id, status, skip=0, limit=10):
        return await self.query_orders(post_office_id=post_id, status=status, skip=skip, limit=limit)

    async def getbyPickupStatus(self, post_id, pickup_status, skip=0, limit=10):
        return await self.query_orders(post_office_id=post_id, pickup_status=pickup_status, skip=skip, limit=limit)

    async def getbyStatusPickStatus(self, post_id, status, pickup_status, skip=0, limit=10):
        return await self.query_orders(post_office_id=post_id, status=status, pickup_status=pickup_status, skip=skip, limit=limit)