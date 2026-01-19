# app/presentation/routes.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from application.services.order_service import OrderService


router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


class OrderCreateRequest(BaseModel):
    priority: str  # "urgent" hoặc "normal"
    customer_name: str
    customer_phone: str
    pickup_address: dict
    delivery_address: dict
    items: List[dict]
    total_amount: Optional[float] = None
    notes: Optional[str] = ""


@router.post("/")
async def create_order(request: OrderCreateRequest):

    service = OrderService()
    order = service.create_order(request.dict())

    return {
        "success": True,
        "data": {
            "order_id": order["id"],
            "order_code": order["order_code"],
            "priority": order["priority"],
            "status": order["status"]
        }
    }


@router.get("/pending")
async def get_pending_orders(priority: Optional[str] = None):
    service = OrderService()
    orders = service.get_pending_orders(priority)
    return {"success": True, "data": orders}


@router.patch("/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    service = OrderService()
    order = service.update_order_status(order_id, status)
    return {"success": True, "data": order}