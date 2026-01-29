# presentation/api/routes.py
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional, Dict, List
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


class GetOrdersRequest(BaseModel):
    """Request để lấy danh sách đơn hàng"""
    post_office_id: str
    status: Optional[str] = "pending"  # pending, scheduled, completed, failed


class GetOrdersByAreaRequest(BaseModel):
    """Request để lấy đơn hàng theo vùng"""
    post_office_id: str
    area_code: str
    status: Optional[str] = "pending"


# Dependency injection
def get_order_processing_service() -> OrderProcessingService:
    """Tạo OrderProcessingService với dependencies"""
    db_client = Database.get_client()

    order_repo = OrderRepository(db_client, schema="delivery")
    schedule_repo = ScheduleRepository(db_client, schema="delivery")
    schedule_item_repo = ScheduleItemRepository(db_client, schema="delivery")

    return OrderProcessingService(
        order_repo=order_repo,
        schedule_repo=schedule_repo,
        schedule_item_repo=schedule_item_repo
    )


@router.post("/list-with-priority")
async def get_orders_with_priority(
        request: GetOrdersRequest,
        service: OrderProcessingService = Depends(get_order_processing_service)
):
    """
    API lấy tất cả đơn hàng với priority score

    - Lấy order_details theo post_office_id
    - Sắp xếp theo priority_score giảm dần
    - Có thể filter theo status

    Returns:
        List các order_details với priority_score
    """
    try:
        orders = await service.order_repo.get_all_orders_with_priority(
            post_office_id=request.post_office_id,
            status=request.status
        )

        return {
            "success": True,
            "total": len(orders),
            "data": [
                {
                    "id": order.id,
                    "order_id": order.order_id,
                    "start_point": order.start_point,
                    "address_detail": order.address_detail,
                    "area_code": order.area_code,
                    "priority_score": order.priority_score,
                    "status": order.status,
                    "location": order.location
                }
                for order in orders
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy danh sách đơn hàng: {str(e)}"
        )


@router.post("/group-by-area")
async def get_orders_grouped_by_area(
        request: GetOrdersRequest,
        service: OrderProcessingService = Depends(get_order_processing_service)
):
    """
    API lấy đơn hàng và nhóm theo area_code

    - Lấy tất cả order_details
    - Nhóm theo area_code
    - Mỗi area có danh sách orders đã sắp xếp theo priority

    Returns:
        Dict với key là area_code, value là list orders
    """
    try:
        grouped_orders = await service.order_repo.get_orders_grouped_by_area(
            post_office_id=request.post_office_id,
            status=request.status
        )

        # Format response
        result = {}
        total_orders = 0

        for area_code, orders in grouped_orders.items():
            total_orders += len(orders)
            result[area_code] = {
                "area_code": area_code,
                "total_orders": len(orders),
                "orders": [
                    {
                        "id": order.id,
                        "order_id": order.order_id,
                        "start_point": order.start_point,
                        "address_detail": order.address_detail,
                        "priority_score": order.priority_score,
                        "status": order.status,
                    }
                    for order in orders
                ]
            }

        return {
            "success": True,
            "total_areas": len(result),
            "total_orders": total_orders,
            "data": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi nhóm đơn hàng theo vùng: {str(e)}"
        )


@router.post("/list-by-area")
async def get_orders_by_area(
        request: GetOrdersByAreaRequest,
        service: OrderProcessingService = Depends(get_order_processing_service)
):
    """
    API lấy đơn hàng của một vùng cụ thể

    Returns:
        List orders của vùng đó, sắp xếp theo priority
        Trả về empty list nếu không có đơn hàng
    """
    try:
        orders = await service.order_repo.get_orders_by_area(
            post_office_id=request.post_office_id,
            area_code=request.area_code,
            status=request.status
        )

        return {
            "success": True,
            "area_code": request.area_code,
            "total": len(orders),
            "data": [
                {
                    "id": order.id,
                    "order_id": order.order_id,
                    "start_point": order.start_point,
                    "address_detail": order.address_detail,
                    "area_code": order.area_code,
                    "priority_score": order.priority_score,
                    "status": order.status,
                }
                for order in orders
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy đơn hàng theo vùng: {str(e)}"
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

    except ValueError as e:
        # ValueError khi không có đơn hàng pending
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
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
        # ValueError khi không có đơn hàng pending cho vùng này
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
        List các schedule items đã được sắp xếp theo queue_number
    """
    try:
        items = await service.schedule_item_repo.get_items_by_schedule(schedule_id)

        return {
            "success": True,
            "total": len(items),
            "data": [item.dict() for item in items]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy schedule items: {str(e)}"
        )