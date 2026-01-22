from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from database import engine

router = APIRouter(prefix="/orders", tags=["Orders"])

class CancelOrderRequest(BaseModel):
    order_id: int

@router.post("/cancel")
def cancel_order(data: CancelOrderRequest):
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    UPDATE orders
                    SET status = 'cancelled'
                    WHERE id = :order_id
                      AND status NOT IN ('completed', 'cancelled')
                """),
                {
                    "order_id": data.order_id
                }
            )

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Order cannot be cancelled"
                )

        return {
            "message": "Order cancelled successfully",
            "order_id": data.order_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
