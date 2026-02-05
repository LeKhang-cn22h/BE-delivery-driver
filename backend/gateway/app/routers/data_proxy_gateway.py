from fastapi import APIRouter, Request, HTTPException, Query
import os
import sys

# Add root path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.http_client import HTTPClient

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics Data Proxy"]
)

# ==============================
# CONFIG
# ==============================
ANALYTICS_SERVICE_URL = os.getenv(
    "ANALYTICS_SERVICE_URL",
    "http://analytics_api:5000"  # docker service name
)

analytics_client = HTTPClient(ANALYTICS_SERVICE_URL)


# ==============================
# ROUTES - CÁC API MỚI
# ==============================

@router.get("/location-pairs", summary="Phân tích các cặp điểm xuất hiện cùng nhau")
async def location_pairs(
        min_support: float = Query(0.01, ge=0.001, le=1, description="Ngưỡng support tối thiểu"),
        limit: int = Query(50, ge=1, le=200, description="Số lượng cặp tối đa")
):
    """
    Proxy tới analytics_api /api/location-pairs

    Trả về các cặp điểm (pickup-delivery) xuất hiện cùng nhau với:
    - Support: Tần suất xuất hiện
    - Confidence: Độ tin cậy
    - Lift: Độ nâng cao (>2.0 = RẤT thường, >1.5 = Thường)
    - Prediction: Dự đoán và khuyến nghị
    - Suggested location: Vị trí đề xuất mở bưu cục
    """
    try:
        return await analytics_client.get(
            "/api/location-pairs",
            params={
                "min_support": min_support,
                "limit": limit
            }
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Analytics service error: {str(e)}")


@router.get("/post-office-suggestions", summary="Gợi ý vị trí mở bưu cục mới")
async def post_office_suggestions(
        min_support: float = Query(0.02, ge=0.001, le=1, description="Ngưỡng support tối thiểu"),
        top_n: int = Query(10, ge=1, le=50, description="Số lượng gợi ý")
):
    """
    Proxy tới analytics_api /api/post-office-suggestions

    Gợi ý vị trí mở bưu cục dựa trên phân tích cặp điểm:
    - 🔴 Rất cao: Lift > 2.0 và Confidence > 70% - NÊN MỞ NGAY
    - 🟠 Cao: Lift > 1.5 và Confidence > 50% - Nên cân nhắc
    - 🟡 Trung bình: Lift > 1.2 - Có thể xem xét
    - 🟢 Thấp: Ưu tiên thấp
    """
    try:
        return await analytics_client.get(
            "/api/post-office-suggestions",
            params={
                "min_support": min_support,
                "top_n": top_n
            }
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Analytics service error: {str(e)}")


@router.get("/location-hotspots", summary="Xác định các điểm HOT (nhiều đơn nhất)")
async def location_hotspots(
        top_n: int = Query(20, ge=5, le=100, description="Số lượng điểm top")
):
    """
    Proxy tới analytics_api /api/location-hotspots

    Xác định các điểm có lượng đơn hàng nhiều nhất:
    - Pickup count: Số đơn lấy hàng tại điểm này
    - Delivery count: Số đơn giao đến điểm này
    - Total orders: Tổng số đơn
    - Pickup ratio: Tỷ lệ đơn pickup so với tổng
    """
    try:
        return await analytics_client.get(
            "/api/location-hotspots",
            params={"top_n": top_n}
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Analytics service error: {str(e)}")


# ==============================
# ROUTES - API CŨ (Giữ lại để tương thích ngược)
# ==============================

@router.get("/route-analysis", summary="[LEGACY] Phân tích tuyến đường (Apriori)")
async def route_analysis(
        min_support: float = 0.01,
        min_confidence: float = 0.1,
        limit: int = 50
):
    """
    LEGACY API - Giữ lại để tương thích ngược

    ⚠️ KHUYẾN NGHỊ: Sử dụng /api/analytics/location-pairs thay thế
    """
    try:
        return await analytics_client.get(
            "/api/route-analysis",
            params={
                "min_support": min_support,
                "min_confidence": min_confidence,
                "limit": limit
            }
        )
    except Exception as e:
        # Fallback to location-pairs if route-analysis not available
        try:
            return await analytics_client.get(
                "/api/location-pairs",
                params={
                    "min_support": min_support,
                    "limit": limit
                }
            )
        except:
            raise HTTPException(status_code=502, detail=f"Analytics service error: {str(e)}")


@router.get("/area-stats", summary="[LEGACY] Thống kê pickup / delivery area")
async def area_stats(
        top_n: int = 10
):
    """
    LEGACY API - Giữ lại để tương thích ngược

    ⚠️ KHUYẾN NGHỊ: Sử dụng /api/analytics/location-hotspots thay thế
    """
    try:
        return await analytics_client.get(
            "/api/area-stats",
            params={"top_n": top_n}
        )
    except Exception as e:
        # Fallback to location-hotspots
        try:
            return await analytics_client.get(
                "/api/location-hotspots",
                params={"top_n": top_n}
            )
        except:
            raise HTTPException(status_code=502, detail=f"Analytics service error: {str(e)}")


# ==============================
# HEALTH CHECK
# ==============================

@router.get("/health", summary="Health check analytics service")
async def health_check():
    """
    Kiểm tra trạng thái analytics service
    """
    try:
        response = await analytics_client.get("/health")
        return {
            "status": "healthy",
            "service": "analytics_proxy",
            "analytics_service": response,
            "available_endpoints": {
                "new_apis": [
                    "/api/analytics/location-pairs",
                    "/api/analytics/post-office-suggestions",
                    "/api/analytics/location-hotspots"
                ],
                "legacy_apis": [
                    "/api/analytics/route-analysis",
                    "/api/analytics/area-stats"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Analytics service unavailable: {str(e)}"
        )


@router.get("/info", summary="Thông tin về Analytics API")
async def api_info():
    """
    Thông tin chi tiết về các API endpoints có sẵn
    """
    return {
        "service": "Analytics Data Proxy",
        "version": "2.0.0",
        "description": "Proxy service cho analytics_api với phân tích cặp điểm và gợi ý bưu cục",
        "endpoints": {
            "location_pairs": {
                "path": "/api/analytics/location-pairs",
                "method": "GET",
                "description": "Phân tích các cặp điểm pickup-delivery xuất hiện cùng nhau",
                "params": {
                    "min_support": "Ngưỡng support tối thiểu (0.001-1)",
                    "limit": "Số lượng cặp tối đa (1-200)"
                },
                "response": "Danh sách cặp điểm với lift, confidence, prediction"
            },
            "post_office_suggestions": {
                "path": "/api/analytics/post-office-suggestions",
                "method": "GET",
                "description": "Gợi ý vị trí mở bưu cục dựa trên cặp điểm",
                "params": {
                    "min_support": "Ngưỡng support tối thiểu (0.001-1)",
                    "top_n": "Số lượng gợi ý (1-50)"
                },
                "response": "Danh sách vị trí đề xuất với mức độ ưu tiên"
            },
            "location_hotspots": {
                "path": "/api/analytics/location-hotspots",
                "method": "GET",
                "description": "Các điểm có lượng đơn hàng nhiều nhất",
                "params": {
                    "top_n": "Số lượng điểm top (5-100)"
                },
                "response": "Danh sách điểm hot với pickup/delivery count"
            }
        },
        "migration_guide": {
            "old": "/api/data/route-analysis",
            "new": "/api/analytics/location-pairs",
            "breaking_changes": [
                "Response structure changed from area codes to full locations",
                "Added 'prediction' and 'suggested_office_location' fields",
                "Lift threshold changed: >2.0 (very high), >1.5 (high)"
            ]
        }
    }