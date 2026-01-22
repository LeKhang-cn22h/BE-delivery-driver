from infrastructure.database.repositories import OrderRepository

class CancelOrderUseCase:
    def __init__(self):
        self.repo = OrderRepository()

    def execute(self, order_id: str):
        if not self.repo.cancel(order_id):
            raise ValueError("Cannot cancel order")

        return {
            "message": "Order cancelled",
            "order_id": order_id
        }
