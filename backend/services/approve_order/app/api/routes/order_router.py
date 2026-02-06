from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, Dict, List
from application.services.order_service import OrderProcessingService
from infrastructure.database import Database
from infrastructure.repositories.order_repository import OrderRepository
from infrastructure.repositories.schedule_repository import ScheduleRepository
from infrastructure.repositories.schedule_item_repository import ScheduleItemRepository
from application.dto.schedule_item_dto import GetOrdersByAreaRequest,GetOrdersRequest
router = APIRouter(prefix="/api/orders", tags=["Order Management"])

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
    """Lấy tất cả đơn hàng với priority score"""
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
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@router.post("/group-by-area")
async def get_orders_grouped_by_area(
    request: GetOrdersRequest,
    service: OrderProcessingService = Depends(get_order_processing_service)
):
    """Lấy đơn hàng nhóm theo area_code"""
    try:
        grouped_orders = await service.order_repo.get_orders_grouped_by_area(
            post_office_id=request.post_office_id,
            status=request.status
        )
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
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@router.post("/list-by-area")
async def get_orders_by_area(
    request: GetOrdersByAreaRequest,
    service: OrderProcessingService = Depends(get_order_processing_service)
):
    """Lấy đơn hàng của một vùng cụ thể"""
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
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

@router.get("/schedules")
async def list_schedules(
    post_office_id: Optional[str] = Query(None),
    scheduled_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    area_code: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: OrderProcessingService = Depends(get_order_processing_service)
):
    """Lấy danh sách schedules với thông tin driver"""
    try:
        query = (
            service.schedule_repo.db
            .schema(service.schedule_repo.schema)
            .table("schedules")
            .select("*")
        )
        
        if post_office_id:
            query = query.eq("post_office_id", post_office_id)
        if scheduled_date:
            query = query.eq("scheduled_date", scheduled_date)
        if status:
            query = query.eq("status", status)
        if area_code:
            query = query.eq("area_code", area_code)
        
        query = query.range(skip, skip + limit - 1)
        query = query.order("scheduled_date", desc=True)
        
        response = query.execute()
        schedules = response.data if response.data else []
        
        # Populate driver info
        schedules_with_drivers = await _populate_driver_info(
            schedules, 
            service.schedule_repo.db,
            service.schedule_repo.schema
        )
        
        return {
            "success": True,
            "total": len(schedules_with_drivers),
            "data": schedules_with_drivers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@router.get("/schedules/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    service: OrderProcessingService = Depends(get_order_processing_service)
):
    """Lấy chi tiết một schedule"""
    try:
        schedule = await service.schedule_repo.get_schedule_by_id(schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Không tìm thấy schedule")
        return {
            "success": True,
            "data": schedule.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@router.get("/schedules/{schedule_id}/items")
async def get_schedule_items(
    schedule_id: str,
    service: OrderProcessingService = Depends(get_order_processing_service)
):
    """Lấy danh sách items trong schedule"""
    try:
        items = await service.schedule_item_repo.get_items_by_schedule(schedule_id)
        return {
            "success": True,
            "total": len(items),
            "data": [item.dict() for item in items]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@router.patch("/schedules/{schedule_id}/assign-driver")
async def assign_driver(
    schedule_id: str,
    driver_id: str,
    service: OrderProcessingService = Depends(get_order_processing_service)
):
    """Gán tài xế cho schedule (thủ công)"""
    try:
        response = (
            service.schedule_repo.db
            .schema(service.schedule_repo.schema)
            .table("schedules")
            .update({"driver_id": driver_id})
            .eq("id", schedule_id)
            .execute()
        )
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy schedule")
        
        return {
            "success": True,
            "message": f"Đã gán tài xế {driver_id} cho schedule {schedule_id}",
            "data": response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@router.patch("/schedules/{schedule_id}/status")
async def update_schedule_status(
    schedule_id: str,
    status: str,
    service: OrderProcessingService = Depends(get_order_processing_service)
):
    """Cập nhật trạng thái schedule"""
    valid_statuses = ['draft', 'confirmed', 'in_progress', 'completed', 'cancelled']
    
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Status không hợp lệ. Phải là một trong: {valid_statuses}"
        )
    
    try:
        response = (
            service.schedule_repo.db
            .schema(service.schedule_repo.schema)
            .table("schedules")
            .update({"status": status})
            .eq("id", schedule_id)
            .execute()
        )
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy schedule")
        
        return {
            "success": True,
            "message": f"Đã cập nhật status thành '{status}'",
            "data": response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")


@router.patch("/schedules/{schedule_id}/cancel")
async def cancel_schedule_status(
    schedule_id: str,
    service: OrderProcessingService = Depends(get_order_processing_service)
):
    try:
        response = (
            service.schedule_repo.db
            .schema(service.schedule_repo.schema)
            .table("schedules")
            .update({"status": "cancelled"})
            .eq("id", schedule_id)
            .execute()
        )
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy schedule")
        
        return {
            "success": True,
            "message": f"Đã cập nhật status thành cancelled",
            "data": response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi: {str(e)}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def _populate_driver_info(schedules: List[Dict], db, schema: str) -> List[Dict]:
    """Populate driver info (name, phone) cho danh sách schedules"""
    if not schedules:
        return schedules
    
    # Lấy danh sách driver_id unique
    driver_ids = list(set(
        schedule.get("driver_id") 
        for schedule in schedules 
        if schedule.get("driver_id")
    ))
    
    if not driver_ids:
        return schedules
    
    try:
        # Query tất cả drivers cùng lúc
        drivers_response = (
            db
            .schema(schema)  
            .table("drivers")  
            .select("id, name, phone")
            .in_("id", driver_ids)
            .execute()
        )
        
        drivers_data = drivers_response.data if drivers_response.data else []
        
        # Tạo map để lookup nhanh
        driver_map = {driver["id"]: driver for driver in drivers_data}
        
        # Populate vào schedules
        result = []
        for schedule in schedules:
            schedule_copy = schedule.copy()
            driver_id = schedule_copy.get("driver_id")
            
            if driver_id and driver_id in driver_map:
                driver = driver_map[driver_id]
                schedule_copy["driver_name"] = driver.get("name")
                schedule_copy["driver_phone"] = driver.get("phone")
            
            result.append(schedule_copy)
        
        return result
        
    except Exception:
        # Nếu lỗi, vẫn trả về schedules ban đầu
        return schedules
