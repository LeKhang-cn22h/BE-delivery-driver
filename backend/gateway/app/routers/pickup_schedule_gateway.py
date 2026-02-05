# gateway/routes/pickup_schedule_gateway.py
"""
Gateway routes cho Pickup Schedule endpoints
"""
from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional
import os
import logging

from services.http_client import HTTPClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pickup-schedules", tags=["Pickup Schedules Gateway"])

# URL tới Order Service
ORDERS_SERVICE_URL = os.getenv("ORDERS_SERVICE_URL", "http://orders_service:8002")
pickup_client = HTTPClient(ORDERS_SERVICE_URL)


async def get_user_headers(request: Request) -> dict:
    """Lấy user info từ request.state để forward"""
    headers = {}
    if hasattr(request.state, "user_id"):
        headers["X-User-ID"] = str(request.state.user_id)
    if hasattr(request.state, "user_email"):
        headers["X-User-Email"] = request.state.user_email
    if hasattr(request.state, "user_role"):
        headers["X-User-Role"] = request.state.user_role
    return headers


@router.patch("/{order_id}/assign-driver", summary="Gán tài xế cho đơn PICKUP")
async def assign_pickup_driver(order_id: str, request: Request):
    """
    Gán tài xế cho đơn hàng PICKUP
    
    Body: { "driver_id": "uuid" }
    """
    headers = await get_user_headers(request)
    body = await request.json()
    
    logger.info(f"User {headers.get('X-User-Email')} assign driver for pickup order {order_id}")
    
    return await pickup_client.request(
        "PATCH",
        f"/api/v1/pickup-schedules/{order_id}/assign-driver",
        json_data=body,
        headers=headers
    )


@router.get("/driver/{driver_id}", summary="Lấy danh sách pickup của tài xế")
async def get_driver_pickup_schedules(
    driver_id: str,
    request: Request,
    status: Optional[str] = Query(None, regex="^(scheduled|picked|failed)$")
):
    """
    Lấy danh sách đơn PICKUP được gán cho tài xế
    
    Dùng cho mobile app
    """
    headers = await get_user_headers(request)
    
    params = {}
    if status:
        params["status"] = status
    
    return await pickup_client.request(
        "GET",
        f"/api/v1/pickup-schedules/driver/{driver_id}",
        params=params,
        headers=headers
    )


@router.patch("/{order_id}/update-pickup-status", summary="Cập nhật trạng thái lấy hàng")
async def update_pickup_status(
    order_id: str,
    request: Request,
    new_status: str = Query(..., regex="^(scheduled|picked|failed)$"),
    failure_reason: Optional[str] = Query(None)
):
    """
    Tài xế cập nhật trạng thái lấy hàng từ mobile app
    
    - picked: Đã lấy hàng thành công
    - failed: Không lấy được hàng
    """
    headers = await get_user_headers(request)
    
    params = {"new_status": new_status}
    if failure_reason:
        params["failure_reason"] = failure_reason
    
    logger.info(f"Driver update pickup status for order {order_id} to {new_status}")
    
    return await pickup_client.request(
        "PATCH",
        f"/api/v1/pickup-schedules/{order_id}/update-pickup-status",
        params=params,
        headers=headers
    )