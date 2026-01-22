from infrastructure.database.repositories import OrderRepository

ALLOWED_STATUS = {
    "pending",
    "picked_up",
    "delivering",
    "completed",
    "cancelled"
}

class UpdateOrderStatusUseCase:
    def __init__(self):
        self.repo = OrderRepository()

    async def execute(self, order_id: str, status: str):
        if status not in ALLOWED_STATUS:
            raise ValueError("Invalid status")

        if not self.repo.update_status(order_id, status):
            raise ValueError("Order not found")

        return {
            "message": "Status updated",
            "order_id": order_id,
            "status": status
        }
