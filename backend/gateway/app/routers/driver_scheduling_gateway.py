# gateway/router/driver_scheduling_gateway.py
from fastapi import APIRouter, Request, HTTPException
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.http_client import HTTPClient

router = APIRouter(
    prefix="/api/driver-scheduling",
    tags=["Driver Scheduling"]
)

APPROVE_ORDER_SERVICE_URL = os.getenv(
    "APPROVE_ORDER_SERVICE_URL",
    "http://localhost:4000"
)

scheduling_client = HTTPClient(APPROVE_ORDER_SERVICE_URL)


# ============ MAIN ENDPOINTS ============

@router.post("/schedule", summary="Xếp lịch tài xế với GA")
async def create_driver_schedule(request: Request):
    """
    Tạo lịch làm việc cho tài xế sử dụng thuật toán Genetic Algorithm

    Body example:
    {
      "scheduled_date": "2026-01-29",
      "area_codes": ["HCMQ12"],
      "post_office_id": "uuid",
      "shift_configs": [
        {
          "shift_name": "Ca sáng",
          "start_time": "07:00:00",
          "end_time": "12:00:00",
          "max_orders_per_driver": 15,
          "max_distance_km": 40.0
        }
      ],
      "population_size": 50,
      "generations": 100,
      "mutation_rate": 0.1,
      "crossover_rate": 0.8,
      "elite_size": 5
    }
    """
    body = await request.json()
    return await scheduling_client.post("/api/v1/driver-scheduling/schedule", body)


@router.post("/schedule/quick", summary="Xếp lịch nhanh")
async def quick_schedule(request: Request):
    """
    Xếp lịch nhanh với cấu hình mặc định

    Body example:
    {
      "scheduled_date": "2026-01-29",
      "area_codes": ["HCMQ12"],
      "post_office_id": "uuid"
    }
    """
    body = await request.json()
    return await scheduling_client.post("/api/v1/driver-scheduling/schedule/quick", body)


@router.get("/schedule/{driver_id}/{scheduled_date}", summary="Xem lịch tài xế")
async def get_driver_schedule(driver_id: str, scheduled_date: str):
    """Lấy lịch làm việc của tài xế theo ngày"""
    return await scheduling_client.get(f"/api/v1/driver-scheduling/schedule/{driver_id}/{scheduled_date}")


@router.put("/schedule/{schedule_id}/status", summary="Cập nhật trạng thái schedule")
async def update_schedule_status(schedule_id: str, request: Request):
    """
    Cập nhật trạng thái của schedule

    Body example:
    {
      "status": "confirmed"
    }
    """
    body = await request.json()
    return await scheduling_client.put(
        f"/api/v1/driver-scheduling/schedule/{schedule_id}/status",
        body
    )


# ============ DEBUG ENDPOINTS ============

@router.get("/debug/check-drivers/{post_office_id}/{scheduled_date}", summary="[Debug] Kiểm tra tài xế")
async def debug_check_drivers(post_office_id: str, scheduled_date: str):
    """Debug: Kiểm tra tài xế available"""
    return await scheduling_client.get(
        f"/api/v1/driver-scheduling/debug/check-drivers/{post_office_id}/{scheduled_date}"
    )


@router.get("/debug/check-orders", summary="[Debug] Kiểm tra đơn hàng")
async def debug_check_orders(area_codes: str, post_office_id: str):
    """
    Debug: Kiểm tra đơn hàng

    Query params:
    - area_codes: comma-separated, e.g., "HCMQ12,Q1"
    - post_office_id: uuid
    """
    return await scheduling_client.get(
        f"/api/v1/driver-scheduling/debug/check-orders?area_codes={area_codes}&post_office_id={post_office_id}"
    )


@router.post("/debug/test-full-flow", summary="[Debug] Test full flow")
async def debug_full_flow(request: Request):
    """
    Debug: Test toàn bộ flow như trong repository

    Body example:
    {
      "area_codes": ["HCMQ12"],
      "post_office_id": "uuid",
      "scheduled_date": "2026-01-29"
    }
    """
    body = await request.json()
    return await scheduling_client.post("/api/v1/driver-scheduling/debug/test-full-flow", body)


@router.get("/health", summary="Health check")
async def health_check():
    """Kiểm tra sức khỏe driver scheduling service"""
    try:
        # Try to call a simple endpoint
        response = await scheduling_client.get(
            "/api/v1/driver-scheduling/debug/check-drivers/00000000-0000-0000-0000-000000000000/2026-01-01")
        return {"status": "healthy", "backend": "driver_scheduling_service"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Driver scheduling service unhealthy: {str(e)}")