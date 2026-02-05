from fastapi import APIRouter, Request, HTTPException
import os
import sys

# Add root path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.http_client import HTTPClient

router = APIRouter(
    prefix="/api/data",
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
# ROUTES
# ==============================

@router.get("/route-analysis", summary="Phân tích tuyến đường (Apriori)")
async def route_analysis(
    min_support: float = 0.01,
    min_confidence: float = 0.1
):
    """
    Proxy tới analytics_api /api/route-analysis
    """
    try:
        return await analytics_client.get(
            "/api/route-analysis",
            params={
                "min_support": min_support,
                "min_confidence": min_confidence
            }
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/area-stats", summary="Thống kê pickup / delivery area")
async def area_stats():
    """
    Proxy tới analytics_api /api/area-stats
    """
    try:
        return await analytics_client.get("/api/area-stats")
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/health", summary="Health check analytics service")
async def health_check():
    """
    Health check analytics service
    """
    try:
        response = await analytics_client.get("/health")
        return {
            "status": "healthy",
            "analytics_service": response
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
