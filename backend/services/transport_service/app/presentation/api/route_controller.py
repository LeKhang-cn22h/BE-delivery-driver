from fastapi import APIRouter

from application.use_cases.optimize_route import OptimizeRouteUseCase
from infrastructure.repositories.supabase_order_repository import SupabaseOrderRepository

router = APIRouter()

@router.get("/optimize-route")
def optimize():
    """
    📌 API: /optimize-route

    Luồng xử lý:
    Client
      → Controller
      → UseCase
      →
      → Supabase
    """

    # Khởi tạo repository (infra layer)
    order_repository = SupabaseOrderRepository()

    # Inject repository vào use case
    use_case = OptimizeRouteUseCase(order_repository)

    # Thực thi nghiệp vụ
    return use_case.execute()
