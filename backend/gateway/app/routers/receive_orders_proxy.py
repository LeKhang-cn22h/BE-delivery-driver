from fastapi import APIRouter, Request, HTTPException
from services.http_client import HTTPClient
from typing import Optional
import os

router = APIRouter(prefix="/api/v1/orders", tags=["Receive Orders"])

# Khởi tạo HTTP client cho receive_orders_service
RECEIVE_ORDERS_SERVICE_URL = os.getenv(
    "RECEIVE_ORDERS_SERVICE_URL",
    "http://receive_orders_service:8001"
)
receive_orders_client = HTTPClient(RECEIVE_ORDERS_SERVICE_URL)


@router.post("/", summary="Tạo đơn hàng mới")
async def create_order(request: Request):
    """
    Tạo đơn hàng mới

    Body example:
    ```json
    {
        "priority": "urgent",
        "customer_name": "Nguyễn Văn A",
        "customer_phone": "0901234567",
        "pickup_address": {
            "street": "123 Nguyễn Huệ",
            "district": "Quận 1",
            "city": "TP.HCM"
        },
        "delivery_address": {
            "street": "456 Lê Lợi",
            "district": "Quận 3",
            "city": "TP.HCM"
        },
        "items": [
            {
                "name": "Hàng hóa",
                "quantity": 2,
                "weight": 1.5
            }
        ],
        "total_amount": 150000,
        "notes": "Ghi chú"
    }
    ```
    """
    body = await request.json()
    return await receive_orders_client.post("/api/v1/orders/", body)


@router.get("/pending", summary="Lấy danh sách orders pending")
async def get_pending_orders(priority: Optional[str] = None):
    """
    Lấy danh sách đơn hàng đang pending

    - **priority**: urgent hoặc normal (optional)
    """
    params = {}
    if priority:
        params["priority"] = priority

    return await receive_orders_client.get("/api/v1/orders/pending", params)


@router.get("/{order_id}", summary="Lấy chi tiết đơn hàng")
async def get_order_detail(order_id: str):
    """
    Lấy chi tiết một đơn hàng theo ID
    """
    return await receive_orders_client.get(f"/api/v1/orders/{order_id}")


@router.patch("/{order_id}/status", summary="Cập nhật trạng thái đơn hàng")
async def update_order_status(order_id: str, request: Request):
    """
    Cập nhật trạng thái đơn hàng

    Body example:
    ```json
    {
        "status": "processing"
    }
    ```

    Các trạng thái có thể:
    - pending
    - processing
    - assigned
    - picked_up
    - in_transit
    - delivered
    - cancelled
    """
    body = await request.json()

    if "status" not in body:
        raise HTTPException(status_code=400, detail="Status is required")

    return await receive_orders_client.patch(
        f"/api/v1/orders/{order_id}/status",
        body
    )