from fastapi import APIRouter, Request, HTTPException
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.http_client import HTTPClient

router = APIRouter(
    prefix="/api/approve-orders",  
    tags=["Approve Order Processing"]
)

APPROVE_ORDER_SERVICE_URL = os.getenv(
    "APPROVE_ORDER_SERVICE_URL",
    "http://localhost:4000"
)

order_client = HTTPClient(APPROVE_ORDER_SERVICE_URL)


@router.get("/schedule/{schedule_id}/items", summary="Lấy chi tiết schedule")
async def get_schedule_items(schedule_id: str):
    """Lấy danh sách order_details trong một schedule"""
    return await order_client.get(f"/api/orders/schedule/{schedule_id}/items")


@router.post("/list-with-priority", summary="Lấy đơn hàng với priority")
async def get_orders_with_priority(request: Request):
    """Lấy đơn hàng với priority score"""
    body = await request.json()
    return await order_client.post("/api/orders/list-with-priority", body)


@router.post("/group-by-area", summary="Nhóm đơn hàng theo vùng")
async def get_orders_grouped_by_area(request: Request):
    """Nhóm đơn hàng theo area_code"""
    body = await request.json()
    return await order_client.post("/api/orders/group-by-area", body)


@router.post("/list-by-area", summary="Lấy đơn hàng theo vùng")
async def get_orders_by_area(request: Request):
    """Lấy đơn hàng của một vùng cụ thể"""
    body = await request.json()
    return await order_client.post("/api/orders/list-by-area", body)


@router.post("/process-all", summary="Xử lý tất cả đơn pending")
async def process_all_pending_orders(request: Request):
    """Xử lý tất cả đơn hàng pending"""
    body = await request.json()
    return await order_client.post("/api/orders/process-all", body)


@router.post("/process-by-area", summary="Xử lý đơn theo vùng")
async def process_orders_by_area(request: Request):
    """Xử lý đơn hàng của một vùng cụ thể"""
    body = await request.json()
    return await order_client.post("/api/orders/process-by-area", body)


@router.get("/health", summary="Health check")
async def health_check():
    """Kiểm tra sức khỏe service"""
    try:
        response = await order_client.get("/health")
        return {"status": "healthy", "backend": response}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))