from fastapi import APIRouter, HTTPException
from models.schemas import RouteRequest, RouteResponse, OptimizedRoute
from services.distance_matrix import distance_matrix_service
from services.optimizer import RouteOptimizer
from services.osrm_service import osrm_service
from core.logger import logger

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post("/optimize", response_model=RouteResponse)
async def optimize_route(request: RouteRequest):
    """
    Tối ưu tuyến đường cho danh sách tọa độ
    """
    try:
        # 1. Chuyển đổi locations sang (lng, lat)
        coords = [(loc.lng, loc.lat) for loc in request.locations]
        
        logger.info(f"Optimizing route for {len(coords)} locations")
        
        # 2. Lấy ma trận khoảng cách từ OSRM
        distance_matrix, duration_matrix = distance_matrix_service.get_matrix(coords)
        
        # 3. Tối ưu với OR-Tools
        optimizer = RouteOptimizer(distance_matrix)
        order, total_distance = optimizer.solve(
            start_index=request.start_index,
            end_index=request.end_index
        )
        
        # 4. Sắp xếp lại coords theo thứ tự tối ưu
        optimized_coords = [coords[i] for i in order]
        
        # 5. Lấy route từ OSRM
        route_data = osrm_service.get_route(optimized_coords)
        
        # 6. Tính total duration
        total_duration = 0
        for i in range(len(order) - 1):
            total_duration += duration_matrix[order[i]][order[i + 1]]
        
        return RouteResponse(
            success=True,
            route=OptimizedRoute(
                order=order,
                total_distance=route_data["distance"],
                total_duration=total_duration,
                coordinates=route_data["coordinates"]
            )
        )
        
    except Exception as e:
        logger.error(f"Route optimization error: {e}")
        return RouteResponse(
            success=False,
            error=str(e)
        )

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "routing"}