# gateway/receive_orders_proxy.py
from fastapi import APIRouter, Request
from uuid import UUID
from services.http_client import HTTPClient
import os

router = APIRouter(prefix="/api/driver", tags=["Driver App Gateway"])

RECEIVE_ORDERS_SERVICE_URL = os.getenv(
    "RECEIVE_ORDERS_SERVICE_URL",
    "http://receive_orders_service:8001"
)

driver_client = HTTPClient(RECEIVE_ORDERS_SERVICE_URL)


async def get_user_headers(request: Request) -> dict:
    headers = {}
    if hasattr(request.state, "user_id"):
        headers["X-User-ID"] = str(request.state.user_id)
    if hasattr(request.state, "user_email"):
        headers["X-User-Email"] = request.state.user_email
    if hasattr(request.state, "user_role"):
        headers["X-User-Role"] = request.state.user_role
    return headers


# ================= START SCHEDULE =================
@router.post("/{driver_id}/schedules/{schedule_id}/start")
async def start_schedule(driver_id: UUID, schedule_id: UUID, request: Request):
    headers = await get_user_headers(request)
    return await driver_client.request(
        "POST",
        f"/api/driver/{driver_id}/schedules/{schedule_id}/start",
        headers=headers
    )


# ================= TAKE ORDER =================
@router.post("/{driver_id}/orders/{order_detail_id}/take")
async def take_order(driver_id: UUID, order_detail_id: UUID, request: Request):
    headers = await get_user_headers(request)
    return await driver_client.request(
        "POST",
        f"/api/driver/{driver_id}/orders/{order_detail_id}/take",
        headers=headers
    )


# ================= PICKED UP =================
@router.post("/{driver_id}/orders/{order_detail_id}/picked-up")
async def picked_up(driver_id: UUID, order_detail_id: UUID, request: Request):
    headers = await get_user_headers(request)
    return await driver_client.request(
        "POST",
        f"/api/driver/{driver_id}/orders/{order_detail_id}/picked-up",
        headers=headers
    )


# ================= DELIVERED =================
@router.post("/{driver_id}/orders/{order_detail_id}/delivered")
async def delivered(driver_id: UUID, order_detail_id: UUID, request: Request):
    headers = await get_user_headers(request)
    return await driver_client.request(
        "POST",
        f"/api/driver/{driver_id}/orders/{order_detail_id}/delivered",
        headers=headers
    )


# ================= UPDATE LOCATION =================
@router.post("/{driver_id}/location")
async def update_location(
        driver_id: UUID,
        lat: float,
        lng: float,
        speed: float,
        heading: float,
        request: Request
):
    headers = await get_user_headers(request)
    return await driver_client.request(
        "POST",
        f"/api/driver/{driver_id}/location",
        params={
            "lat": lat,
            "lng": lng,
            "speed": speed,
            "heading": heading,
        },
        headers=headers
    )


# ================= GET SCHEDULE =================
@router.get("/{driver_id}/schedules/{schedule_id}")
async def get_schedule(driver_id: UUID, schedule_id: UUID, request: Request):
    headers = await get_user_headers(request)
    return await driver_client.request(
        "GET",
        f"/api/driver/{driver_id}/schedules/{schedule_id}",
        headers=headers
    )
@router.post("/{driver_id}/schedules/{schedule_id}/end")
async def end_schedule(driver_id: UUID, schedule_id: UUID, request: Request):
    headers = await get_user_headers(request)
    return await driver_client.request(
        "POST",
        f"/api/driver/{driver_id}/schedules/{schedule_id}/end",
        headers=headers
    )


@router.post("/{driver_id}/off-duty")
async def set_off_duty(driver_id: UUID, request: Request):
    headers = await get_user_headers(request)
    return await driver_client.request(
        "POST",
        f"/api/driver/{driver_id}/off-duty",
        headers=headers
    )


@router.post("/{driver_id}/on-duty")
async def set_on_duty(driver_id: UUID, request: Request):
    headers = await get_user_headers(request)
    return await driver_client.request(
        "POST",
        f"/api/driver/{driver_id}/on-duty",
        headers=headers
    )