from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from pydantic import BaseModel
from application.services.approve_service import OrderProcessingService
from infrastructure.database import Database
from infrastructure.repositories.order_repository import OrderRepository
from infrastructure.repositories.schedule_repository import ScheduleRepository
from infrastructure.repositories.schedule_item_repository import ScheduleItemRepository

router = APIRouter(prefix="/api/orders", tags=["Order Processing"])


# Request models
class ProcessOrdersRequest(BaseModel):
    """Request body để xử lý đơn hàng"""
    post_office_id: str
    scheduled_date: datetime


class ProcessOrdersByAreaRequest(BaseModel):
    """Request body để xử lý đơn hàng theo vùng"""
    post_office_id: str
    area_code: str
    scheduled_date: datetime


# Dependency injection
def get_order_processing_service() -> OrderProcessingService:
    """Tạo OrderProcessingService với dependencies"""
    db_client = Database.get_client()

    order_repo = OrderRepository(db_client)
    schedule_repo = ScheduleRepository(db_client)
    schedule_item_repo = ScheduleItemRepository(db_client)

    return OrderProcessingService(
        order_repo=order_repo,
        schedule_repo=schedule_repo,
        schedule_item_repo=schedule_item_repo
    )


@router.post("/process-all")
async def process_all_pending_orders(
        request: ProcessOrdersRequest,
        service: OrderProcessingService = Depends(get_order_processing_service)
):
    """
    API xử lý tất cả đơn hàng pending của một bưu cục

    - Lấy tất cả order_details có status = 'pending'
    - Nhóm theo area_code
    - Tạo schedule cho từng vùng
    - Tạo schedule_items với queue theo priority_score
    - Cập nhật status order_details sang 'scheduled'

    Returns:
        BatchProcessingResult với thông tin các schedules đã tạo
    """
    try:
        result = await service.process_pending_orders(
            post_office_id=request.post_office_id,
            scheduled_date=request.scheduled_date
        )

        return {
            "success": True,
            "message": f"Đã xử lý {result.total_orders} đơn hàng thành {result.total_schedules} lịch trình",
            "data": result.dict()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xử lý đơn hàng: {str(e)}"
        )


@router.post("/process-by-area")
async def process_orders_by_area(
        request: ProcessOrdersByAreaRequest,
        service: OrderProcessingService = Depends(get_order_processing_service)
):
    """
    API xử lý đơn hàng của một vùng cụ thể

    - Lấy order_details theo area_code
    - Tạo schedule cho vùng đó
    - Tạo schedule_items với queue theo priority_score
    - Cập nhật status order_details sang 'scheduled'

    Returns:
        OrderProcessingResult với thông tin schedule đã tạo
    """
    try:
        result = await service.process_orders_by_area(
            post_office_id=request.post_office_id,
            area_code=request.area_code,
            scheduled_date=request.scheduled_date
        )

        return {
            "success": True,
            "message": f"Đã tạo lịch trình cho vùng {request.area_code} với {result.total_orders} đơn hàng",
            "data": result.dict()
        }

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi xử lý đơn hàng: {str(e)}"
        )


@router.get("/schedule/{schedule_id}/items")
async def get_schedule_items(
        schedule_id: str,
        service: OrderProcessingService = Depends(get_order_processing_service)
):
    """
    API lấy danh sách order_details trong một schedule

    Returns:
        List các schedule items đã được sắp xếp theo queue
    """
    try:
        items = await service.schedule_item_repo.get_items_by_schedule(schedule_id)

        return {
            "success": True,
            "data": [item.dict() for item in items]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy schedule items: {str(e)}"
        )