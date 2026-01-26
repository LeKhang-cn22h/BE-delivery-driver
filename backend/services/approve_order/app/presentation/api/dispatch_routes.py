from fastapi import APIRouter
from application.services.approve_service import ApproveOrderService

router = APIRouter(prefix="/dispatch", tags=["Dispatch"])


@router.post("/approve")
def approve_orders():
    return ApproveOrderService.approve_orders_by_area()
