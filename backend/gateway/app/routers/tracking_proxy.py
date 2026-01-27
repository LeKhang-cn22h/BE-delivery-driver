from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional
from uuid import UUID
import os
import httpx

router = APIRouter(prefix="/api/v1/tracking", tags=["Tracking"])

TRACKING_SERVICE_URL = os.getenv("TRACKING_SERVICE_URL", "http://websocket:8007")


async def _proxy_request(method: str, path: str, **kwargs):
    """Helper function để proxy request đến tracking service"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method,
                f"{TRACKING_SERVICE_URL}{path}",
                **kwargs
            )
            return response.json()
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Tracking service timeout")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Tracking service unavailable")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# ================== UPDATE LOCATION ==================

@router.post("/{driver_id}/location", summary="Driver gửi vị trí mới")
async def update_location(driver_id: UUID, request: Request):
    body = await request.json()
    return await _proxy_request(
        "POST",
        f"/api/v1/tracking/{driver_id}/location",
        json=body
    )


# ================== GET CURRENT LOCATION ==================

@router.get("/{driver_id}/current", summary="Lấy vị trí hiện tại của driver")
async def get_current_location(driver_id: UUID):
    return await _proxy_request(
        "GET",
        f"/api/v1/tracking/{driver_id}/current"
    )


# ================== GET HISTORY ==================

@router.get("/{driver_id}/history", summary="Lấy lịch sử di chuyển của driver")
async def get_driver_history(
    driver_id: UUID,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    schedule_id: Optional[UUID] = None,
    limit: int = Query(default=1000, le=5000)
):
    params = {"limit": limit}
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time
    if schedule_id:
        params["schedule_id"] = str(schedule_id)
    
    return await _proxy_request(
        "GET",
        f"/api/v1/tracking/{driver_id}/history",
        params=params
    )


# ================== GET SCHEDULE ROUTE ==================

@router.get("/schedule/{schedule_id}/route", summary="Lấy tuyến đường của lịch giao hàng")
async def get_schedule_route(schedule_id: UUID):
    return await _proxy_request(
        "GET",
        f"/api/v1/tracking/schedule/{schedule_id}/route"
    )


# ================== GET ACTIVE DRIVERS ==================

@router.get("/drivers/active", summary="Lấy danh sách drivers đang hoạt động")
async def get_active_drivers(
    minutes: int = Query(default=5, le=60),
    post_office_id: Optional[UUID] = None
):
    params = {"minutes": minutes}
    if post_office_id:
        params["post_office_id"] = str(post_office_id)
    
    return await _proxy_request(
        "GET",
        f"/api/v1/tracking/drivers/active",
        params=params
    )