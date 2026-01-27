from uuid import UUID
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from supabase_client import get_supabase
from DTO.Location import LocationUpdateDTO
from services.location_service import LocationService
from ws.connection_manager import manager

router = APIRouter(prefix="/api/v1/tracking", tags=["Tracking"])


def get_location_service(supabase: Client = Depends(get_supabase)) -> LocationService:
    return LocationService(supabase)


# ================== UPDATE LOCATION ==================

@router.post("/{driver_id}/location")
async def update_driver_location(
    driver_id: UUID,
    location: LocationUpdateDTO,
    service: LocationService = Depends(get_location_service)
):
    """
    Driver gửi vị trí mới (có áp dụng Data Smoothing):
    1. Luôn cập nhật current_locations (real-time display)
    2. Chỉ lưu vào history nếu đạt threshold (tiết kiệm storage)
    3. Broadcast qua WebSocket
    
    Smoothing filters:
    - Distance: Chỉ lưu khi di chuyển > 10m
    - Time: Force lưu mỗi 30 giây
    - Speed: Loại bỏ điểm có tốc độ > 120 km/h (GPS jump)
    """
    try:
        # Sử dụng method với smoothing
        saved_to_history, reason, broadcast_data = service.update_location_with_smoothing(
            driver_id=driver_id,
            location=location
        )
        
        # Broadcast qua WebSocket
        await manager.broadcast_to_viewers(str(driver_id), broadcast_data)
        await manager.broadcast_to_admins(broadcast_data)
        
        return {
            "status": "ok",
            "saved_to_history": saved_to_history,
            "reason": reason
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================== UPDATE LOCATION (WITHOUT SMOOTHING) ==================

@router.post("/{driver_id}/location/raw")
async def update_driver_location_raw(
    driver_id: UUID,
    location: LocationUpdateDTO,
    service: LocationService = Depends(get_location_service)
):
    """
    Driver gửi vị trí mới (KHÔNG áp dụng smoothing)
    Lưu tất cả điểm vào history - dùng cho debug hoặc high-precision tracking
    """
    try:
        # 1. Cập nhật vị trí hiện tại
        service.update_current_location(driver_id, location)
        
        # 2. Luôn lưu vào history (không smoothing)
        service.save_location_history(driver_id, location)
        
        # 3. Broadcast qua WebSocket
        broadcast_data = service.build_broadcast_data(driver_id, location)
        broadcast_data["saved_to_history"] = True
        broadcast_data["save_reason"] = "raw_mode"
        
        await manager.broadcast_to_viewers(str(driver_id), broadcast_data)
        await manager.broadcast_to_admins(broadcast_data)
        
        return {
            "status": "ok",
            "saved_to_history": True,
            "reason": "raw_mode"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ================== GET CURRENT LOCATION ==================

@router.get("/{driver_id}/current")
def get_current_location(
    driver_id: UUID,
    service: LocationService = Depends(get_location_service)
):
    """Lấy vị trí hiện tại của driver"""
    result = service.get_current_location(driver_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Driver location not found")
    
    return result


# ================== GET HISTORY ==================

@router.get("/{driver_id}/history")
def get_driver_history(
    driver_id: UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    schedule_id: Optional[UUID] = None,
    limit: int = Query(default=1000, le=5000),
    service: LocationService = Depends(get_location_service)
):
    """Lấy lịch sử di chuyển của driver (dữ liệu gốc từ database)"""
    return service.get_driver_history(
        driver_id=driver_id,
        start_time=start_time,
        end_time=end_time,
        schedule_id=schedule_id,
        limit=limit
    )


# ================== GET HISTORY COMPRESSED ==================

@router.get("/{driver_id}/history/compressed")
def get_driver_history_compressed(
    driver_id: UUID,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    epsilon: float = Query(default=0.00005, description="Ngưỡng nén Douglas-Peucker (càng nhỏ càng chi tiết)"),
    service: LocationService = Depends(get_location_service)
):
    """
    Lấy lịch sử di chuyển đã được NÉN bằng thuật toán Douglas-Peucker
    
    Useful for:
    - Hiển thị tuyến đường trên map (giảm số điểm vẽ)
    - Export data (giảm dung lượng file)
    - Phân tích tuyến đường (loại bỏ noise)
    
    Args:
        epsilon: Ngưỡng nén
            - 0.0001: Nén mạnh, ít điểm
            - 0.00005: Nén vừa (default)
            - 0.00001: Nén nhẹ, nhiều điểm
    
    Returns:
        - original_count: Số điểm gốc
        - compressed_count: Số điểm sau nén
        - compression_ratio: Tỉ lệ nén
        - points: Danh sách điểm đã nén
    """
    return service.get_driver_history_compressed(
        driver_id=driver_id,
        start_time=start_time,
        end_time=end_time,
        epsilon=epsilon
    )


# ================== GET SCHEDULE ROUTE ==================

@router.get("/schedule/{schedule_id}/route")
def get_schedule_route(
    schedule_id: UUID,
    service: LocationService = Depends(get_location_service)
):
    """Lấy toàn bộ tuyến đường của 1 lịch giao hàng"""
    return service.get_schedule_route(schedule_id)


# ================== GET ACTIVE DRIVERS ==================

@router.get("/drivers/active")
def get_active_drivers(
    minutes: int = Query(default=5, le=60),
    post_office_id: Optional[UUID] = None,
    service: LocationService = Depends(get_location_service)
):
    """Lấy tất cả drivers đang hoạt động (có cập nhật trong X phút)"""
    return service.get_active_drivers(minutes=minutes, post_office_id=post_office_id)


# ================== SET DRIVER OFFLINE ==================

@router.post("/{driver_id}/offline")
def set_driver_offline(
    driver_id: UUID,
    service: LocationService = Depends(get_location_service)
):
    """
    Đánh dấu driver offline
    - Clear smoother cache
    - Update status trong database
    """
    try:
        service.set_driver_offline(driver_id)
        return {"status": "ok", "message": f"Driver {driver_id} marked as offline"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))