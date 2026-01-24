# app/application/use_cases/update_order_status.py
from domain.repositories.order_repository import OrderRepository


class UpdateOrderStatusUseCase:
    """
    Cập nhật trạng thái đơn hàng
    """

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, order_id: str, new_status: str) -> bool:
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError(f"Không tìm thấy đơn hàng {order_id}")

        # Cập nhật status
        return await self.order_repository.update_status(order_id, new_status)
