from fastapi import APIRouter, Request, HTTPException
from services.http_client import HTTPClient
from typing import Optional
import os
import logging


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/order", tags=["Receive Orders"])

# Khởi tạo HTTP client cho receive_orders_service
RECEIVE_ORDERS_SERVICE_URL = os.getenv(
    "RECEIVE_ORDERS_SERVICE_URL",
    "http://receive_orders_service:8001"
)
receive_orders_client = HTTPClient(RECEIVE_ORDERS_SERVICE_URL)

async def get_user_headers(request: Request) -> dict:
    """
    Extract user info từ request.state (được set bởi AuthMiddleware)
    và add vào headers để forward đến backend service
    
    Backend service sẽ nhận:
    - X-User-ID: UUID của user
    - X-User-Email: Email
    - X-User-Role: Role (admin, dispatcher, driver, customer)
    """
    headers = {}
    
    if hasattr(request.state, "user_id"):
        headers["X-User-ID"] = str(request.state.user_id)
    
    if hasattr(request.state, "user_email"):
        headers["X-User-Email"] = request.state.user_email
    
    if hasattr(request.state, "user_role"):
        headers["X-User-Role"] = request.state.user_role
    
    return headers

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
    headers= await get_user_headers(request)

    logger.info(f"Creating order for user: {headers.get('X-User-Email')}")

    return await receive_orders_client.request(
        "POST",
        "/api/v1/order/",
        json_data=body,
        headers=headers
    )

@router.get("/pending", summary="Lấy danh sách orders pending")
async def get_pending_orders(request:Request,priority: Optional[str] = None):
    """
    Lấy danh sách đơn hàng đang pending

    - **priority**: urgent hoặc normal (optional)
    """
    params = {}
    if priority:
        params["priority"] = priority
    
    headers = await get_user_headers(request)


    return await receive_orders_client.request(
        "GET",
        "/api/v1/orders/pending",
        params=params,
        headers=headers
    )

@router.get("/{order_id}", summary="Lấy chi tiết đơn hàng")
async def get_order_detail(request: Request,order_id: str):
    """
    Lấy chi tiết một đơn hàng theo ID
    """
    headers= await get_user_headers(request)
    return await receive_orders_client.request(
        "GET",
        f"/api/v1/orders/{order_id}",
        headers=headers
    )

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

    headers=await get_user_headers(request)
    logger.info(
        f"User {headers.get('X-User-Email')} updating order {order_id} "
        f"to status: {body['status']}"
    )
    return await receive_orders_client.request(
        "PATCH",
        f"/api/v1/orders/{order_id}/status",
        json_data=body,
        headers=headers
    )