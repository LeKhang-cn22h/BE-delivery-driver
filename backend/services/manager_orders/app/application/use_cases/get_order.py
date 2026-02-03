from domain.entities.order import Order
from domain.repositories.order_detail_repository import OrderDetailRepository
from domain.repositories.order_repository import OrderRepository
from typing import List

class GetOrderUseCase:
    """
    Lấy chi tiết đơn hàng (bao gồm tất cả kiện hàng)
    """

    def __init__(
            self,
            order_repository: OrderRepository,
            order_detail_repository: OrderDetailRepository
    ):
        self.order_repository = order_repository
        self.order_detail_repository = order_detail_repository

    async def execute(self, order_id: str) -> Order:
        # Lấy thông tin đơn hàng
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError(f"Không tìm thấy đơn hàng {order_id}")

        # Lấy tất cả kiện hàng trong đơn
        order_details = await self.order_detail_repository.get_by_order_id(order_id)
        order.order_details = order_details

        return order
    
    async def getbyPost(self, post_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy đơn hàng theo post office"""
        return await self.order_repository.get_by_postid(post_id, skip, limit)

    async def getbyStatus(self, post_id: str, status: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy đơn hàng theo status"""
        return await self.order_repository.get_by_post_status(post_id, status, skip, limit)

    async def getbyPickupStatus(self, post_id: str, pickup_status: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy đơn hàng theo pickup status"""
        return await self.order_repository.get_by_pickupStatus(post_id, pickup_status, skip, limit)

    async def getbyStatusPickStatus(self, post_id: str, status: str, pickup_status: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy đơn hàng theo cả status và pickup status"""
        return await self.order_repository.get_by_pickupStatus_status(post_id, status, pickup_status, skip, limit)