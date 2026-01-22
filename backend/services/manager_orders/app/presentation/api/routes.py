from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from application.use_cases.create_order import CreateOrderUseCase
from application.use_cases.update_order_status import UpdateOrderStatusUseCase
from application.use_cases.cancel_order import CancelOrderUseCase

router = APIRouter(prefix="/orders", tags=["Orders"])


class CreateOrderRequest(BaseModel):
    user_id: str
    pickup_point: str


class UpdateStatusRequest(BaseModel):
    order_id: str
    status: str


class CancelOrderRequest(BaseModel):
    order_id: str


@router.post("/create")
def create_order(data: CreateOrderRequest):
    try:
        return CreateOrderUseCase().execute(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/update-status")
def update_status(data: UpdateStatusRequest):
    try:
        return UpdateOrderStatusUseCase().execute(
            data.order_id, data.status
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cancel")
def cancel_order(data: CancelOrderRequest):
    try:
        return CancelOrderUseCase().execute(data.order_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
