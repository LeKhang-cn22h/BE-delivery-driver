from infrastructure.database.repositories import OrderRepository

class CreateOrderUseCase:
    def __init__(self):
        self.repo = OrderRepository()

    async def execute(self, data):
        order_id = self.repo.create(
            data.user_id,
            data.pickup_point
        )

        return {
            "message": "Order created",
            "order_id": order_id,
            "status": "pending"
        }
