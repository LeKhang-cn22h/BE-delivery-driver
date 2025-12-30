from domain.repositories.order_repository import OrderRepository

class OptimizeRouteUseCase:
    """
    📌 Use Case:
    - Lấy orders
    - Chạy thuật toán TSP
    - Trả về thứ tự giao hàng tối ưu
    """

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    def execute(self):
        # Lấy orders từ repository
        orders = self.order_repository.get_all()

        # TODO: Chỗ này cắm thuật toán TSP
        # optimized_orders = tsp_solver(orders)

        return orders