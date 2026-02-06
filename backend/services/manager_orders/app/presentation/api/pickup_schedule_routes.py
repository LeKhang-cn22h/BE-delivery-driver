# presentation/api/pickup_schedule_routes.py
"""
API endpoints để quản lý lịch lấy hàng (PICKUP)
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

router = APIRouter(prefix="/api/v1/pickup-schedules", tags=["Pickup Schedules"])


class AssignPickupDriverRequest(BaseModel):
    driver_id: str


@router.patch("/{order_id}/assign-driver")
async def assign_pickup_driver(
    order_id: str,
    request: AssignPickupDriverRequest
):
    """
    Gán tài xế cho đơn hàng PICKUP
    
    Flow:
    1. Kiểm tra order có phải PICKUP không
    2. Kiểm tra tài xế có available không
    3. Cập nhật pickup_driver_id cho order
    4. Cập nhật pickup_status = 'scheduled'
    5. (Optional) Tạo notification cho tài xế
    """
    from infrastructure.database.supabase_client import SupabaseClient
    
    client = SupabaseClient.get_client()
    
    try:
        # Step 1: Kiểm tra order
        order_response = (
            client.schema("delivery")
            .table("orders")
            .select("*")
            .eq("id", order_id)
            .single()
            .execute()
        )
        
        if not order_response.data:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
        
        order = order_response.data
        
        if order["order_type"] != "pickup":
            raise HTTPException(
                status_code=400, 
                detail="Chỉ có thể gán tài xế cho đơn PICKUP"
            )
        
        if order["status"] != "confirmed":
            raise HTTPException(
                status_code=400,
                detail="Đơn hàng chưa được duyệt"
            )
        
        # Step 2: Kiểm tra tài xế
        driver_response = (
            client.schema("delivery")
            .table("drivers")
            .select("*")
            .eq("id", request.driver_id)
            .single()
            .execute()
        )
        
        if not driver_response.data:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài xế")
        
        driver = driver_response.data
        
        if driver["status"] not in ["available", "busy"]:
            raise HTTPException(
                status_code=400,
                detail=f"Tài xế không khả dụng (status: {driver['status']})"
            )
        
        # Step 3: Gán tài xế
        update_response = (
            client.schema("delivery")
            .table("orders")
            .update({
                "pickup_driver_id": request.driver_id,
                "pickup_status": "scheduled"
            })
            .eq("id", order_id)
            .execute()
        )
        
        return {
            "success": True,
            "message": "Đã gán tài xế thành công",
            "order_id": order_id,
            "driver_id": request.driver_id,
            "pickup_status": "scheduled"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi gán tài xế: {str(e)}"
        )


@router.get("/driver/{driver_id}")
async def get_driver_pickup_schedules(
    driver_id: str,
    status: Optional[str] = Query(None, pattern="^(scheduled|picked|failed)$")
):
    """
    Lấy danh sách đơn PICKUP được gán cho tài xế
    
    Dùng cho mobile app của tài xế
    """
    from infrastructure.database.supabase_client import SupabaseClient
    
    client = SupabaseClient.get_client()
    
    try:
        query = (
            client.schema("delivery")
            .table("orders")
            .select("*")
            .eq("pickup_driver_id", driver_id)
            .eq("order_type", "pickup")
        )
        
        if status:
            query = query.eq("pickup_status", status)
        
        response = query.order("created_at", desc=True).execute()
        
        return {
            "success": True,
            "total": len(response.data),
            "data": response.data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi lấy danh sách: {str(e)}"
        )


@router.patch("/{order_id}/update-pickup-status")
async def update_pickup_status(
    order_id: str,
    new_status: str = Query(
        ..., 
        pattern="^(scheduled|picked|failed)$",
        description="Trạng thái mới: scheduled, picked, failed"
    ),
    failure_reason: Optional[str] = Query(None, description="Lý do thất bại nếu status=failed")
):
    """
    Cập nhật trạng thái lấy hàng
    
    Được gọi từ mobile app của tài xế khi:
    - Đã lấy hàng thành công -> picked
    - Không lấy được hàng -> failed
    """
    from infrastructure.database.supabase_client import SupabaseClient
    
    client = SupabaseClient.get_client()
    
    try:
        update_data = {"pickup_status": new_status}
        
        if new_status == "failed" and failure_reason:
            update_data["pickup_failure_reason"] = failure_reason
        
        response = (
            client.schema("delivery")
            .table("orders")
            .update(update_data)
            .eq("id", order_id)
            .execute()
        )
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")
        
        return {
            "success": True,
            "message": f"Đã cập nhật trạng thái: {new_status}",
            "order_id": order_id,
            "pickup_status": new_status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi cập nhật: {str(e)}"
        )