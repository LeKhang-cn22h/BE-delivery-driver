from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.http_client import HTTPClient

router = APIRouter(
    prefix="/api/v1/routing",
    tags=["Routing"]
)

ROUTING_SERVICE_URL = os.getenv(
    "ROUTING_SERVICE_URL",
    "http://routing_service:8386"  # Tên container trong docker-compose

)
routing_client = HTTPClient(ROUTING_SERVICE_URL)

@router.post("/optimize", summary="Tối ưu tuyến đường")
async def optimize_route(request: Request):
    """
    Tối ưu tuyến đường cho danh sách tọa độ

    **Request body:**
    ```json
    {
        "locations": [
            {"lat": 10.7769, "lng": 106.7009, "name": "TP.HCM"},
            {"lat": 10.8231, "lng": 106.6297, "name": "Tân Bình"}
        ],
        "start_index": 0
    }
    ```
    """
    body = await request.json()
    return await routing_client.post("/api/v1/routes/optimize", body)
@router.get("/health", summary="Kiểm tra sức khỏe dịch vụ định tuyến")
async def health_check():
    """
    Kiểm tra sức khỏe dịch vụ định tuyến
    """
    return await routing_client.get("/api/v1/routes/health")
