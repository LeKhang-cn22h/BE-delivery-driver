# app/application/use_cases/list_customer_orders.py
from typing import List

from domain.entities.order import Order
from domain.repositories.order_detail_repository import OrderDetailRepository
from domain.repositories.order_repository import OrderRepository


class ListCustomerOrdersUseCase:
    """
    Khách hàng xem lịch sử đơn hàng của mình
    """

    def __init__(
            self,
            order_repository: OrderRepository,
            order_detail_repository: OrderDetailRepository
    ):
        self.order_repository = order_repository
        self.order_detail_repository = order_detail_repository

    async def execute(self, user_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        # Lấy danh sách đơn hàng
        orders = await self.order_repository.get_by_user_id(user_id, skip, limit)

        # Load kiện hàng cho từng đơn
        for order in orders:
            order_details = await self.order_detail_repository.get_by_order_id(order.id)
            order.order_details = order_details

        return orders