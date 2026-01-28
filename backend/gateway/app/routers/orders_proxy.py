from fastapi import APIRouter, Request, HTTPException, Query
from uuid import UUID

from typing import Optional
import os
import logging

from services.http_client import HTTPClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/orders", tags=["Orders Gateway"])
routerP = APIRouter(prefix="/api/v1/post_offices", tags=["Post Offices Gateway"])
routerD = APIRouter(prefix="/api/v1/drivers", tags=["Drivers Gateway"])
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


# ================================
# POST OFFICE ENDPOINTS
# ================================
@routerP.get("/{post_office_id}", summary="Lấy thông tin bưu cục theo ID")
async def get_post_office(post_office_id: UUID):
    try:
        return await orders_client.request(
            "GET",
            f"/api/v1/post_offices/{post_office_id}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@routerP.get("/area/{area_code}", summary="Lấy danh sách bưu cục theo mã vùng")
async def get_post_offices_by_area_code(area_code: str):
    return await orders_client.request(
        "GET",
        f"/api/v1/post_offices/area/{area_code}"
    )


@routerP.post("/", summary="Tạo bưu cục mới")
async def create_post_office(request: Request):
    body = await request.json()
    return await orders_client.request(
        "POST",
        "/api/v1/post_offices/",
        json_data=body
    )


@routerP.patch("/{post_office_id}/status/activate", summary="Cập nhật activate trạng thái bưu cục")
async def update_post_office_ac(post_office_id: UUID):
    try:
        return await orders_client.request(
            "PATCH",
            f"/api/v1/post_offices/{post_office_id}/status/activate",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@routerP.patch("/{post_office_id}/status/deactivate", summary="Cập nhật trạng thái deactivate bưu cục")
async def update_post_office_status(post_office_id: UUID):
    try:
        return await orders_client.request(
            "PATCH",
            f"/api/v1/post_offices/{post_office_id}/status/deactivate",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# driver endpoints proxy
@routerD.get("/{driver_id}", summary="Lấy thông tin tài xế theo ID")
async def get_driver(driver_id: UUID):
    try:
        return await orders_client.request(
            "GET",
            f"/api/v1/drivers/{driver_id}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@routerD.get("/post_office/{post_office_id}", summary="Lấy danh sách tài xế theo ID bưu cục")
async def get_drivers_by_post_office_id(post_office_id: UUID):
    try:
        return await orders_client.request(
            "GET",
            f"/api/v1/drivers/post_office/{post_office_id}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@routerD.get("/status/{status}", summary="Lấy danh sách tài xế theo trạng thái")
async def get_drivers_by_status(status: str):
    try:
        return await orders_client.request(
            "GET",
            f"/api/v1/drivers/status/{status}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@routerD.post("/", summary="Tạo tài xế mới")
async def create_driver(request: Request):
    body = await request.json()
    try:
        return await orders_client.request(
            "POST",
            "/api/v1/drivers/",
            json_data=body
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
@routerD.patch("/{driver_id}", summary="Cập nhật thông tin tài xế")
async def update_driver(driver_id: UUID, request: Request):
    body = await request.json()
    try:
        return await orders_client.request(
            "PATCH",
            f"/api/v1/drivers/{driver_id}",
            json_data=body
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
@routerD.patch("/{driver_id}/available", summary="Cập nhật trạng thái tài xế thành available")
async def update_driver_available(driver_id: UUID):
    try:
        return await orders_client.request(
            "PATCH",
            f"/api/v1/drivers/{driver_id}/available"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
@routerD.patch("/{driver_id}/busy", summary="Cập nhật trạng thái tài xế thành busy")
async def update_driver_busy(driver_id: UUID):
    try:
        return await orders_client.request(
            "PATCH",
            f"/api/v1/drivers/{driver_id}/busy"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@routerD.patch("/{driver_id}/off_duty", summary="cập nhật trạng thái tài xế off_duty")
async def update_driver_off_duty(driver_id:UUID):
    try:
        return await orders_client.request(
            "PATCH",
            f"/api/v1/drivers/{driver_id}/off_duty"
        )
    except ValueError as e:
        raise HTTPException(status=500, detail=str(e))
    
@routerD.patch("/{driver_id}/inactive", summary="Cập nhật trạng thái tài xế thành inactive")
async def update_driver_inactive(driver_id: UUID):
    try:
        return await orders_client.request(
            "PATCH",
            f"/api/v1/drivers/{driver_id}/inactive"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
