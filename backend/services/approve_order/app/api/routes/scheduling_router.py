from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from application.dto.scheduling_dto import SchedulingRequest, SchedulingResponse, SchedulingQuickRequest
from application.services.ga_scheduling_service import GASchedulingService
from infrastructure.database import Database

router = APIRouter(prefix="/api/scheduling", tags=["GA Scheduling"])

def get_scheduling_service():
    """Tạo GASchedulingService"""
    supabase = Database.get_client(schema="delivery")
    return GASchedulingService(supabase)


def get_supabase_client():
    """Lấy Supabase client cho debug endpoints"""
    return Database.get_client(schema="delivery")


@router.post("/create", response_model=SchedulingResponse)
async def create_schedule_with_ga(
    request: SchedulingRequest, 
    service: GASchedulingService = Depends(get_scheduling_service)
):
    """
    1. Lấy đơn hàng confirmed theo area_codes
    2. Chạy GA để gom đơn thành schedules
    3. Tạo schedules (KHÔNG gán driver)
    """
    try:
        result = await service.create_schedules(request)
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
    requestfe:SchedulingQuickRequest,
    service: GASchedulingService = Depends(get_scheduling_service)
):
    """
    Xếp lịch nhanh với cấu hình mặc định
    
    **Cấu hình mặc định:**
    - Max 15 đơn/schedule
    - GA: population=50, generations=100
    """
    try:
        request = SchedulingRequest(
            scheduled_date=requestfe.scheduled_date,
            area_codes=requestfe.area_codes,
            post_office_id=requestfe.post_office_id
        )
        
        result = await service.create_schedules(request)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi xếp lịch nhanh: {str(e)}"
        )

