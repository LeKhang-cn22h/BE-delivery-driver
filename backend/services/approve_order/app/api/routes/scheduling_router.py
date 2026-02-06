# api/routes/scheduling_router.py
"""
Router cho GA Scheduling
ĐÃ LOẠI BỎ: shift config, time-based scheduling
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from datetime import date
from pydantic import BaseModel

from application.dto.scheduling_dto import SchedulingRequest, SchedulingResponse
from application.services.ga_scheduling_service import GASchedulingService
from infrastructure.database import Database

router = APIRouter(prefix="/api/v1/scheduling", tags=["GA Scheduling"])


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_scheduling_service():
    """Tạo GASchedulingService"""
    supabase = Database.get_client(schema="delivery")
    return GASchedulingService(supabase)


def get_supabase_client():
    """Lấy Supabase client cho debug endpoints"""
    return Database.get_client(schema="delivery")


# ============================================================================
# REQUEST MODELS
# ============================================================================

class CreateScheduleRequest(BaseModel):
    """Request để tạo schedule bằng GA"""
    scheduled_date: date
    area_codes: List[str]
    post_office_id: UUID
    
    # Schedule constraints
    max_orders_per_schedule: int = 15
    max_distance_km: float = 40.0
    
    # GA parameters (optional)
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    elite_size: int = 5


class DebugFlowRequest(BaseModel):
    """Request để debug flow"""
    area_codes: List[str]
    post_office_id: UUID
    scheduled_date: date


# ============================================================================
# SCHEDULING ENDPOINTS
# ============================================================================

@router.post("/create", response_model=SchedulingResponse)
async def create_schedule_with_ga(
    request: CreateScheduleRequest,
    service: GASchedulingService = Depends(get_scheduling_service)
):
    """
    Tạo schedule bằng Genetic Algorithm
    
    **Flow:**
    1. Lấy đơn hàng pending theo area_codes
    2. Chạy GA để tối ưu (gom đơn, tối ưu route)
    3. Tạo schedules (KHÔNG gán driver)
    
    **Việc gán tài xế thực hiện thủ công qua:**
    `PATCH /api/orders/schedules/{id}/assign-driver`
    """
    try:
        scheduling_request = SchedulingRequest(
            scheduled_date=request.scheduled_date,
            area_codes=request.area_codes,
            post_office_id=request.post_office_id,
            max_orders_per_schedule=request.max_orders_per_schedule,
            max_distance_km=request.max_distance_km,
            population_size=request.population_size,
            generations=request.generations,
            mutation_rate=request.mutation_rate,
            crossover_rate=request.crossover_rate,
            elite_size=request.elite_size
        )
        
        result = await service.create_schedules(scheduling_request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xếp lịch: {str(e)}"
        )


@router.post("/create-quick", response_model=SchedulingResponse)
async def create_schedule_quick(
    scheduled_date: date,
    area_codes: List[str],
    post_office_id: UUID,
    service: GASchedulingService = Depends(get_scheduling_service)
):
    """
    Xếp lịch nhanh với cấu hình mặc định
    
    **Cấu hình mặc định:**
    - Max 15 đơn/schedule
    - Max 40km khoảng cách
    - GA: population=50, generations=100
    """
    try:
        scheduling_request = SchedulingRequest(
            scheduled_date=scheduled_date,
            area_codes=area_codes,
            post_office_id=post_office_id,
            max_orders_per_schedule=15,
            max_distance_km=40.0,
            population_size=50,
            generations=100,
            mutation_rate=0.1,
            crossover_rate=0.8,
            elite_size=5
        )
        
        result = await service.create_schedules(scheduling_request)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xếp lịch nhanh: {str(e)}"
        )


# ============================================================================
# DEBUG ENDPOINTS
# ============================================================================

@router.get("/debug/drivers/{post_office_id}/{scheduled_date}")
async def debug_check_drivers(
    post_office_id: UUID,
    scheduled_date: date,
    supabase=Depends(get_supabase_client)
):
    """Debug: Kiểm tra tài xế của bưu cục"""
    try:
        drivers = (
            supabase.schema("delivery").table("drivers")
            .select("*")
            .eq("post_office_id", str(post_office_id))
            .execute()
        ).data

        schedules = (
            supabase.schema("delivery").table("schedules")
            .select("*")
            .eq("scheduled_date", str(scheduled_date))
            .execute()
        ).data

        return {
            "success": True,
            "data": {
                "total_drivers": len(drivers),
                "drivers": drivers,
                "total_schedules": len(schedules),
                "schedules": schedules
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/orders")
async def debug_check_orders(
    area_codes: str,  # comma-separated
    post_office_id: UUID,
    supabase=Depends(get_supabase_client)
):
    """Debug: Kiểm tra đơn hàng theo khu vực"""
    try:
        area_list = area_codes.split(",")

        order_details = (
            supabase.schema("delivery").table("order_details")
            .select("*")
            .in_("area_code", area_list)
            .execute()
        ).data

        return {
            "success": True,
            "data": {
                "total_order_details": len(order_details),
                "order_details": order_details,
                "analysis": {
                    "pending": len([od for od in order_details if od.get("status") == "pending"]),
                    "scheduled": len([od for od in order_details if od.get("status") == "scheduled"]),
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/debug/test-flow")
async def debug_test_full_flow(
    request: DebugFlowRequest,
    supabase=Depends(get_supabase_client)
):
    """Debug: Test flow lấy đơn hàng"""
    area_codes = request.area_codes
    post_office_id = request.post_office_id

    result = {
        "step_1_order_details": {},
        "step_2_filter_by_orders": {},
        "step_3_filter_by_schedule_items": {},
        "final_result": []
    }

    try:
        # Step 1: Query order_details
        order_details = (
            supabase.schema("delivery").table("order_details")
            .select("id, order_id, start_point, address_detail, area_code, location, priority_score, status")
            .in_("area_code", area_codes)
            .eq("status", "pending")
            .execute()
        ).data

        result["step_1_order_details"] = {
            "query": f"area_code IN {area_codes} AND status = 'pending'",
            "count": len(order_details),
        }

        if not order_details:
            result["message"] = "Không có order_details pending"
            return {"success": True, "data": result}

        # Step 2: Filter by orders
        passed_step2 = []
        for od in order_details:
            order = (
                supabase.schema("delivery").table("orders")
                .select("id, post_office_id, status")
                .eq("id", od["order_id"])
                .execute()
            ).data

            if not order:
                continue

            order = order[0]
            if order["post_office_id"] == str(post_office_id) and \
               order["status"] in ["confirmed", "processing"]:
                passed_step2.append(od)

        result["step_2_filter_by_orders"] = {
            "total_checked": len(order_details),
            "passed": len(passed_step2),
        }

        if not passed_step2:
            result["message"] = "Không có order nào thỏa mãn"
            return {"success": True, "data": result}

        # Step 3: Check schedule_items
        final_result = []
        for od in passed_step2:
            schedule_items = (
                supabase.schema("delivery").table("schedule_items")
                .select("id, schedule_id")
                .eq("order_detail_id", od["id"])
                .execute()
            ).data

            if not schedule_items:
                final_result.append(od)
                continue

            # Check active schedule
            has_active = False
            for si in schedule_items:
                schedule = (
                    supabase.schema("delivery").table("schedules")
                    .select("status")
                    .eq("id", si["schedule_id"])
                    .in_("status", ["draft", "confirmed", "in_progress"])
                    .execute()
                ).data

                if schedule:
                    has_active = True
                    break

            if not has_active:
                final_result.append(od)

        result["step_3_filter_by_schedule_items"] = {
            "total_checked": len(passed_step2),
            "available": len(final_result),
        }

        result["final_result"] = final_result
        result["message"] = f"Tìm thấy {len(final_result)} đơn có thể xếp lịch"

        return {"success": True, "data": result}

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
