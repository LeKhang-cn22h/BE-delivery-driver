# app/application/use_cases/get_order.py
from domain.entities.order import Order
from domain.repositories.order_detail_repository import OrderDetailRepository
from domain.repositories.order_repository import OrderRepository


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