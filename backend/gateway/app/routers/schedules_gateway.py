# routers/schedules_gateway.py
"""
Gateway cho Schedule Management endpoints
Proxy requests đến approve_order_service
"""
from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional
from uuid import UUID
import os
import logging

from services.http_client import HTTPClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/schedules", tags=["Schedules Management"])

# URL tới Approve Order Service (có schedule repository)
APPROVE_ORDER_SERVICE_URL = os.getenv(
    "APPROVE_ORDER_SERVICE_URL",
    "http://approve_order_service:4000"
)

schedules_client = HTTPClient(APPROVE_ORDER_SERVICE_URL)


async def get_user_headers(request: Request) -> dict:
    """Lấy user info từ request.state"""
    headers = {}
    if hasattr(request.state, "user_id"):
        headers["X-User-ID"] = str(request.state.user_id)
    if hasattr(request.state, "user_email"):
        headers["X-User-Email"] = request.state.user_email
    if hasattr(request.state, "user_role"):
        headers["X-User-Role"] = request.state.user_role
    return headers


# ================================
# GET SCHEDULES LIST
# ================================
@router.get("/", summary="Lấy danh sách schedules")
async def list_schedules(
    request: Request,
    post_office_id: Optional[str] = Query(None),
    scheduled_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    area_code: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Lấy danh sách schedules với filters
    
    Query params:
    - post_office_id: Filter theo bưu cục
    - scheduled_date: Filter theo ngày (YYYY-MM-DD)
    - status: draft, confirmed, in_progress, completed, cancelled
    - area_code: Filter theo khu vực
    """
    headers = await get_user_headers(request)
    
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
    
    return await schedules_client.request(
        "GET",
        "/api/orders/schedules",
        params=params,
        headers=headers
    )


# ================================
# GET SCHEDULE DETAIL
# ================================
@router.get("/{schedule_id}", summary="Lấy chi tiết schedule")
async def get_schedule_detail(schedule_id: str, request: Request):
    """Lấy thông tin chi tiết một schedule"""
    headers = await get_user_headers(request)
    
    return await schedules_client.request(
        "GET",
        f"/api/orders/schedules/{schedule_id}",
        headers=headers
    )


# ================================
# ASSIGN DRIVER
# ================================
@router.patch("/{schedule_id}/assign-driver", summary="Gán tài xế cho schedule")
async def assign_driver_to_schedule(schedule_id: str, request: Request):
    """
    Gán tài xế cho schedule
    
    Body: { "driver_id": "uuid" }
    """
    headers = await get_user_headers(request)
    body = await request.json()
    
    logger.info(f"Assigning driver to schedule {schedule_id}: {body.get('driver_id')}")
    
    return await schedules_client.request(
        "PATCH",
        f"/api/orders/schedules/{schedule_id}/assign-driver",
        json_data=body,
        headers=headers
    )


# ================================
# UPDATE STATUS
# ================================
@router.patch("/{schedule_id}/status", summary="Cập nhật trạng thái schedule")
async def update_schedule_status(schedule_id: str, request: Request):
    """
    Cập nhật trạng thái schedule
    
    Body: { "status": "confirmed" | "in_progress" | "completed" | "cancelled" }
    """
    headers = await get_user_headers(request)
    body = await request.json()
    
    logger.info(f"Updating schedule {schedule_id} status to: {body.get('status')}")
    
    return await schedules_client.request(
        "PATCH",
        f"/api/orders/schedules/{schedule_id}/status",
        json_data=body,
        headers=headers
    )


# ================================
# CANCEL SCHEDULE
# ================================
@router.patch("/{schedule_id}/cancel", summary="Hủy schedule")
async def cancel_schedule(schedule_id: str, request: Request):
    """
    Hủy schedule
    
    Body: { "reason": "string" }
    """
    headers = await get_user_headers(request)
    body = await request.json()
    
    logger.info(f"Cancelling schedule {schedule_id}, reason: {body.get('reason')}")
    
    return await schedules_client.request(
        "PATCH",
        f"/api/orders/schedules/{schedule_id}/cancel",
        json_data=body,
        headers=headers
    )


# ================================
# GET SCHEDULE ITEMS
# ================================
@router.get("/{schedule_id}/items", summary="Lấy danh sách items trong schedule")
async def get_schedule_items(schedule_id: str, request: Request):
    """Lấy danh sách order_details trong schedule"""
    headers = await get_user_headers(request)
    
    return await schedules_client.request(
        "GET",
        f"/api/orders/schedules/{schedule_id}/items",
        headers=headers
    )


# ================================
# STATISTICS
# ================================
@router.get("/stats/overview", summary="Thống kê schedules")
async def get_schedules_statistics(
    request: Request,
    post_office_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    Thống kê tổng quan schedules
    
    Query params:
    - post_office_id: Filter theo bưu cục
    - start_date, end_date: Khoảng thời gian
    """
    headers = await get_user_headers(request)
    
    params = {}
    if post_office_id:
        params["post_office_id"] = post_office_id
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    return await schedules_client.request(
        "GET",
        "/api/orders/schedules/stats/overview",
        params=params,
        headers=headers
    )