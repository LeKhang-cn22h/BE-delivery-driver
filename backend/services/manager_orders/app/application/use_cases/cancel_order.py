# app/application/use_cases/cancel_order.py
from domain.entities.order import OrderStatus
from domain.repositories.order_repository import OrderRepository


class CancelOrderUseCase:
    """
    Khách hàng hủy đơn hàng (chỉ được hủy khi chưa lấy hàng)
    """

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    async def execute(self, order_id: str, user_id: str, reason: str = None) -> bool:
        # Lấy đơn hàng
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError(f"Không tìm thấy đơn hàng {order_id}")

        # Kiểm tra quyền (chỉ chủ đơn mới hủy được)
        if order.user_id != user_id:
            raise ValueError("Bạn không có quyền hủy đơn hàng này")

        # Kiểm tra có thể hủy không
        if not order.can_cancel():
            raise ValueError(f"Không thể hủy đơn hàng ở trạng thái {order.status.value}")

        # Cập nhật trạng thái
        order.status = OrderStatus.CANCELLED

        await self.order_repository.update(order)
        return True
