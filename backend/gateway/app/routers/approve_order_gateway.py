from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional
import os
import sys
import logging

logger = logging.getLogger(__name__)

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
3
order_client = HTTPClient(APPROVE_ORDER_SERVICE_URL)

@router.get("/health", summary="Health check")
async def health_check():
    """Kiểm tra sức khỏe service"""
    try:
        response = await order_client.get("/health")
        return {"status": "healthy", "backend": response}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

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



@router.get("/", summary="Lấy danh sách schedules với thông tin driver")
async def list_schedules(
    request: Request,
    post_office_id: Optional[str] = Query(None),
    scheduled_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    area_code: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Lấy danh sách schedules với filters"""    
    params = {"skip": skip, "limit": limit}
    if post_office_id:
        params["post_office_id"] = post_office_id
    if scheduled_date:
        params["scheduled_date"] = scheduled_date
    if status:
        params["status"] = status
    if area_code:
        params["area_code"] = area_code
    
    logger.info(f"Listing schedules with filters: {params}")
    
    return await order_client.get(
        "/api/orders/schedules",
        params=params
    )

@router.get("/schedule/{schedule_id}/items", summary="Lấy chi tiết schedule")
async def get_schedule_items(schedule_id: str):
    """Lấy danh sách order_details trong một schedule"""
    return await order_client.get(f"/api/orders/schedule/{schedule_id}/items")


@router.patch("/{schedule_id}/assign-driver", summary="Gán tài xế cho schedule")
async def assign_driver_to_schedule(schedule_id: str, request: Request):
    """Gán tài xế cho schedule"""
    body = await request.json()
    logger.info(f"Assigning driver to schedule {schedule_id}: {body.get('driver_id')}")
    
    return await order_client.patch(
        f"/api/orders/schedules/{schedule_id}/assign-driver",
        json_data=body
    )

@router.patch("/{schedule_id}/status", summary="Cập nhật trạng thái schedule")
async def update_schedule_status(schedule_id: str, request: Request):
    """Cập nhật trạng thái schedule"""
    body = await request.json()
    logger.info(f"Updating schedule {schedule_id} status to: {body.get('status')}")
    
    return await order_client.patch(
        f"/api/orders/schedules/{schedule_id}/status",
        json_data=body
    )

@router.patch("/{schedule_id}/cancel", summary="Hủy schedule")
async def cancel_schedule(schedule_id: str):    
    return await order_client.patch(f"/api/orders/schedules/{schedule_id}/cancel")

@router.get("/schedules/{schedule_id}", summary="lấy chi tiết 1 schedule")
async def get_schedule(schedule_id:str):
    return await order_client.get(f"/api/orders/schedules/{schedule_id}")

@router.post("/schedule", summary="Tạo schedule với GA (không gán driver)")
async def create_schedule_with_ga(request: Request):
    body = await request.json()
    logger.info(f"Creating schedule with GA: {body}")
    return await order_client.post("/api/scheduling/create", body)


@router.post("/schedule-quick", summary="Tạo schedule nhanh với cấu hình mặc định")
async def create_schedule_quick(request: Request):

    body = await request.json()
    logger.info(f"Creating quick schedule: {body}")
    return await order_client.post("/api/scheduling/create-quick", body)
