# app/application/use_cases/create_order.py
from typing import List
from domain.entities.order import Order, OrderDetail, OrderStatus, DetailStatus
from domain.repositories.order_repository import OrderRepository
from domain.repositories.order_detail_repository import OrderDetailRepository


class CreateOrderUseCase:
    """
    Use case: Khách hàng tạo đơn hàng mới
    Flow:
    1. Khách nhập thông tin lấy hàng (pickup)
    2. Khách nhập danh sách kiện hàng cần giao (có thể nhiều địa chỉ khác nhau)
    3. Hệ thống tạo 1 order + nhiều order_details
    """

    def __init__(
            self,
            order_repository: OrderRepository,
            order_detail_repository: OrderDetailRepository
    ):
        self.order_repository = order_repository
        self.order_detail_repository = order_detail_repository

    async def execute(self, order: Order) -> Order:
        # Validate đơn hàng
        order.validate()

        # Set trạng thái ban đầu
        order.status = OrderStatus.PENDING

        # Set trạng thái cho từng kiện hàng
        for detail in order.order_details:
            detail.status = DetailStatus.PENDING

        # Tạo order trước
        created_order = await self.order_repository.create(order)

        # Gán order_id cho các details
        for detail in order.order_details:
            detail.order_id = created_order.id

        # Tạo tất cả order_details
        created_details = await self.order_detail_repository.create_batch(
            order.order_details
        )

        created_order.order_details = created_details
        return created_order