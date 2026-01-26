from fastapi import APIRouter, Request, HTTPException, Query

from typing import Optional
import os
import logging

from services.http_client import HTTPClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/orders", tags=["Orders Gateway"])

# URL tới Order Service (port 8002)
ORDERS_SERVICE_URL = os.getenv(
    "ORDERS_SERVICE_URL",
    "http://orders_service:8002"
)

orders_client = HTTPClient(ORDERS_SERVICE_URL)


async def get_user_headers(request: Request) -> dict:
    """
    Lấy user info từ request.state (AuthMiddleware) để forward sang service backend
    """
    headers = {}

    if hasattr(request.state, "user_id"):
        headers["X-User-ID"] = str(request.state.user_id)

    if hasattr(request.state, "user_email"):
        headers["X-User-Email"] = request.state.user_email

    if hasattr(request.state, "user_role"):
        headers["X-User-Role"] = request.state.user_role

    return headers


# ================================
# CREATE ORDER
# ================================
@router.post("/", summary="Tạo đơn hàng mới")
async def create_order(request: Request):
    body = await request.json()
    headers = await get_user_headers(request)

    logger.info(f"Creating order for user: {headers.get('X-User-Email')}")

    return await orders_client.request(
        "POST",
        "/api/v1/orders/",
        json_data=body,
        headers=headers
    )


# ================================
# GET ORDER DETAIL
# ================================
@router.get("/{order_id}", summary="Lấy chi tiết đơn hàng")
async def get_order_detail(order_id: str, request: Request):
    headers = await get_user_headers(request)

    return await orders_client.request(
        "GET",
        f"/api/v1/orders/{order_id}",
        headers=headers
    )


# ================================
# LIST CUSTOMER ORDERS
# ================================
@router.get("/customer/{user_id}", summary="Lấy danh sách đơn hàng của khách")
async def list_customer_orders(
    user_id: str,
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    headers = await get_user_headers(request)

    params = {
        "skip": skip,
        "limit": limit
    }

    return await orders_client.request(
        "GET",
        f"/api/v1/orders/customer/{user_id}",
        params=params,
        headers=headers
    )


# ================================
# CANCEL ORDER
# ================================
@router.post("/{order_id}/cancel", summary="Hủy đơn hàng")
async def cancel_order(
    order_id: str,
    request: Request,
    user_id: str = Query(...),
    reason: Optional[str] = Query(None),
):
    headers = await get_user_headers(request)

    params = {
        "user_id": user_id
    }
    if reason:
        params["reason"] = reason

    logger.info(
        f"User {headers.get('X-User-Email')} cancel order {order_id}, reason={reason}"
    )

    return await orders_client.request(
        "POST",
        f"/api/v1/orders/{order_id}/cancel",
        params=params,
        headers=headers
    )


# ================================
# UPDATE ORDER STATUS
# ================================
@router.patch("/{order_id}/status", summary="Cập nhật trạng thái đơn hàng")
async def update_order_status(
    order_id: str,
    request: Request,
    new_status: str = Query(
        ...,
        regex="^(pending|confirmed|picking_up|picked_up|in_transit|delivering|completed|cancelled)$"
    ),
):
    headers = await get_user_headers(request)

    logger.info(
        f"User {headers.get('X-User-Email')} update order {order_id} to {new_status}"
    )

    return await orders_client.request(
        "PATCH",
        f"/api/v1/orders/{order_id}/status",
        params={"new_status": new_status},
        headers=headers
    )
