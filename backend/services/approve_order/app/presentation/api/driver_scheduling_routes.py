from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from datetime import date

from application.dto.driver_shift_dto import (
    SchedulingRequest,
    SchedulingResponse,
    ShiftConfig
)
from application.services.driver_shift_scheduling_service import DriverShiftSchedulingService
from infrastructure.database import Database

router = APIRouter(prefix="/api/v1/driver-scheduling", tags=["Driver Scheduling"])


# Dependency để lấy service
def get_scheduling_service():
    supabase = Database.get_client(schema="delivery")
    return DriverShiftSchedulingService(supabase)


def get_supabase_client():
    return Database.get_client(schema="delivery")


@router.post("/schedule", response_model=SchedulingResponse)
async def create_driver_schedule(
        request: SchedulingRequest,
        service: DriverShiftSchedulingService = Depends(get_scheduling_service)
):
    """
    Tạo lịch làm việc cho tài xế sử dụng thuật toán GA

    **Parameters:**
    - **scheduled_date**: Ngày cần xếp lịch
    - **area_codes**: Danh sách mã khu vực cần phân đơn
    - **post_office_id**: ID của bưu cục
    - **shift_configs**: Cấu hình các ca làm việc
    - **population_size**: Kích thước quần thể GA (mặc định: 50)
    - **generations**: Số thế hệ GA (mặc định: 100)
    - **mutation_rate**: Tỷ lệ đột biến (mặc định: 0.1)
    - **crossover_rate**: Tỷ lệ lai ghép (mặc định: 0.8)
    - **elite_size**: Số cá thể ưu tú được giữ lại (mặc định: 5)

    **Returns:**
    - Kết quả xếp lịch bao gồm:
        - Danh sách phân công cho từng tài xế
        - Tổng số đơn đã xếp
        - Danh sách đơn chưa được xếp
        - Điểm fitness
        - Thông tin thuật toán
    """
    try:
        result = await service.schedule_shifts(request)
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


@router.get("/schedule/{driver_id}/{scheduled_date}")
async def get_driver_schedule(
        driver_id: UUID,
        scheduled_date: date,
        service: DriverShiftSchedulingService = Depends(get_scheduling_service)
):
    """
    Lấy lịch làm việc của tài xế theo ngày

    **Parameters:**
    - **driver_id**: ID của tài xế
    - **scheduled_date**: Ngày cần xem lịch

    **Returns:**
    - Thông tin lịch làm việc của tài xế
    """
    try:
        schedule = await service.get_driver_schedule(driver_id, scheduled_date)
        return schedule
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lấy lịch: {str(e)}"
        )


@router.put("/schedule/{schedule_id}/status")
async def update_schedule_status(
        schedule_id: UUID,
        status_value: str,
        service: DriverShiftSchedulingService = Depends(get_scheduling_service)
):
    """
    Cập nhật trạng thái của schedule

    **Parameters:**
    - **schedule_id**: ID của schedule
    - **status**: Trạng thái mới (draft, confirmed, in_progress, completed)

    **Returns:**
    - Thông báo thành công
    """
    valid_statuses = ['draft', 'confirmed', 'in_progress', 'completed']
    if status_value not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Trạng thái không hợp lệ. Phải là một trong: {valid_statuses}"
        )

    try:
        await service.update_schedule_status(schedule_id, status_value)
        return {"message": "Cập nhật trạng thái thành công"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi cập nhật trạng thái: {str(e)}"
        )


@router.post("/schedule/quick")
async def quick_schedule(
        scheduled_date: date,
        area_codes: List[str],
        post_office_id: UUID,
        service: DriverShiftSchedulingService = Depends(get_scheduling_service)
):
    """
    Xếp lịch nhanh với cấu hình mặc định

    **Parameters:**
    - **scheduled_date**: Ngày cần xếp lịch
    - **area_codes**: Danh sách mã khu vực
    - **post_office_id**: ID bưu cục

    **Returns:**
    - Kết quả xếp lịch với cấu hình mặc định
    """
    # Tạo cấu hình ca mặc định
    default_shifts = [
        ShiftConfig(
            shift_name="Ca sáng",
            start_time="07:00:00",
            end_time="12:00:00",
            max_orders_per_driver=15,
            max_distance_km=40.0
        ),
        ShiftConfig(
            shift_name="Ca chiều",
            start_time="13:00:00",
            end_time="18:00:00",
            max_orders_per_driver=15,
            max_distance_km=40.0
        )
    ]

    request = SchedulingRequest(
        scheduled_date=scheduled_date,
        area_codes=area_codes,
        post_office_id=post_office_id,
        shift_configs=default_shifts,
        population_size=50,
        generations=100,
        mutation_rate=0.1,
        crossover_rate=0.8,
        elite_size=5
    )

    try:
        result = await service.schedule_shifts(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xếp lịch nhanh: {str(e)}"
        )


# ============ DEBUG ENDPOINTS ============

@router.get("/debug/check-drivers/{post_office_id}/{scheduled_date}")
async def debug_check_drivers(
        post_office_id: UUID,
        scheduled_date: date,
        supabase=Depends(get_supabase_client)
):
    """Debug: Kiểm tra tài xế available"""
    try:
        # Query drivers
        drivers = (
            supabase.schema("delivery").table("drivers")
            .select("*")
            .eq("post_office_id", str(post_office_id))
            .execute()
        ).data

        # Query schedules cho ngày đó
        schedules = (
            supabase.schema("delivery").table("schedules")
            .select("*")
            .eq("scheduled_date", str(scheduled_date))
            .execute()
        ).data

        return {
            "total_drivers": len(drivers),
            "drivers": drivers,
            "total_schedules": len(schedules),
            "schedules": schedules
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/debug/check-orders")
async def debug_check_orders(
        area_codes: str,  # comma-separated: "HCMQ12,Q1"
        post_office_id: UUID,
        supabase=Depends(get_supabase_client)
):
    """Debug: Kiểm tra đơn hàng"""
    try:
        area_list = area_codes.split(",")

        # Query order_details
        order_details = (
            supabase.schema("delivery").table("order_details")
            .select("*")
            .in_("area_code", area_list)
            .execute()
        ).data

        # Query orders
        if order_details:
            order_ids = [od["order_id"] for od in order_details]
            orders = (
                supabase.schema("delivery").table("orders")
                .select("*")
                .in_("id", order_ids)
                .execute()
            ).data
        else:
            orders = []

        # Query schedule_items
        if order_details:
            od_ids = [od["id"] for od in order_details]
            schedule_items = (
                supabase.schema("delivery").table("schedule_items")
                .select("*")
                .in_("order_detail_id", od_ids)
                .execute()
            ).data
        else:
            schedule_items = []

        return {
            "total_order_details": len(order_details),
            "order_details": order_details,
            "total_orders": len(orders),
            "orders": orders,
            "total_schedule_items": len(schedule_items),
            "schedule_items": schedule_items,
            "analysis": {
                "pending_order_details": len([od for od in order_details if od.get("status") == "pending"]),
                "confirmed_orders": len([o for o in orders if o.get("status") in ["confirmed", "processing"]]),
                "matching_post_office": len([o for o in orders if o.get("post_office_id") == str(post_office_id)])
            }
        }
    except Exception as e:
        return {"error": str(e)}


from pydantic import BaseModel


class DebugFlowRequest(BaseModel):
    area_codes: List[str]
    post_office_id: UUID
    scheduled_date: date


@router.post("/debug/test-full-flow")
async def debug_full_flow(
        request: DebugFlowRequest,
        supabase=Depends(get_supabase_client)
):
    """Debug: Test toàn bộ flow như trong repository"""
    area_codes = request.area_codes
    post_office_id = request.post_office_id
    scheduled_date = request.scheduled_date

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
            .select("id, order_id, start_point, price, address_detail, area_code, location, priority_score, status")
            .in_("area_code", area_codes)
            .eq("status", "pending")
            .execute()
        ).data

        result["step_1_order_details"] = {
            "query": f"area_code IN {area_codes} AND status = 'pending'",
            "count": len(order_details),
            "data": order_details
        }

        if not order_details:
            result["message"] = "STOP: Không có order_details nào với area_code và status=pending"
            return result

        # Step 2: Filter by orders
        passed_step2 = []
        step2_details = []
        for od in order_details:
            order = (
                supabase.schema("delivery").table("orders")
                .select("id, post_office_id, status, pickup_location, pickup_point")
                .eq("id", od["order_id"])
                .limit(1)
                .execute()
            ).data

            if not order or len(order) == 0:
                step2_details.append({
                    "order_detail_id": od["id"],
                    "reason": "Order not found"
                })
                continue

            order = order[0]

            check = {
                "order_detail_id": od["id"],
                "order_id": order["id"],
                "has_order": True,
                "post_office_match": order["post_office_id"] == str(post_office_id),
                "post_office_actual": order["post_office_id"],
                "post_office_expected": str(post_office_id),
                "status_valid": order["status"] in ["confirmed", "processing"],
                "status_actual": order["status"]
            }

            step2_details.append(check)

            if check["post_office_match"] and check["status_valid"]:
                od["pickup_location"] = order.get("pickup_location")
                od["pickup_point"] = order.get("pickup_point")
                passed_step2.append(od)

        result["step_2_filter_by_orders"] = {
            "total_checked": len(order_details),
            "passed": len(passed_step2),
            "required_post_office_id": str(post_office_id),
            "required_status": ["confirmed", "processing"],
            "details": step2_details
        }

        if not passed_step2:
            result["message"] = "STOP: Không có order nào thỏa mãn post_office_id và status"
            return result

        # Step 3: Check schedule_items
        final_result = []
        step3_details = []
        for od in passed_step2:
            schedule_items = (
                supabase.schema("delivery").table("schedule_items")
                .select("id, schedule_id")
                .eq("order_detail_id", od["id"])
                .execute()
            ).data

            check = {
                "order_detail_id": od["id"],
                "has_schedule_items": len(schedule_items) > 0 if schedule_items else False,
                "schedule_items_count": len(schedule_items) if schedule_items else 0
            }

            if not schedule_items or len(schedule_items) == 0:
                check["has_active_schedule"] = False
                final_result.append(od)
            else:
                # Check if schedule is active
                has_active = False
                for si in schedule_items:
                    schedule = (
                        supabase.schema("delivery").table("schedules")
                        .select("status")
                        .eq("id", si["schedule_id"])
                        .in_("status", ["draft", "confirmed", "in_progress"])
                        .limit(1)
                        .execute()
                    ).data

                    if schedule and len(schedule) > 0:
                        has_active = True
                        check["active_schedule_status"] = schedule[0]["status"]
                        break

                check["has_active_schedule"] = has_active

                if not has_active:
                    final_result.append(od)

            step3_details.append(check)

        result["step_3_filter_by_schedule_items"] = {
            "total_checked": len(passed_step2),
            "with_active_schedule": len(passed_step2) - len(final_result),
            "without_active_schedule": len(final_result),
            "details": step3_details
        }

        result["final_result"] = final_result
        result["message"] = f"SUCCESS: Tìm thấy {len(final_result)} đơn hàng có thể xếp lịch"

        return result

    except Exception as e:
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()
        return result