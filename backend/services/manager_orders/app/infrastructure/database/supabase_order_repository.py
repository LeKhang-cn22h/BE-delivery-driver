# app/infrastructure/repositories/supabase_order_repository.py
from typing import List, Optional
from datetime import datetime

from infrastructure.database.supabase_client import SupabaseClient
from domain.repositories.order_repository import OrderRepository
from domain.entities.order import Order, OrderStatus, OrderType


class SupabaseOrderRepository(OrderRepository):
    def __init__(self):
        self.client = SupabaseClient.get_client()
        self.schema = "delivery"
        self.table_name = "orders"

    def _table(self):
        return self.client.schema(self.schema).table(self.table_name)

    def _point_to_db(self, p):
        if p is None:
            return None
        return f"({p.lng},{p.lat})"

    def _point_from_db(self, p):
        if p is None:
            return None
        if isinstance(p, str):
            p = p.strip("()")
            lng, lat = map(float, p.split(","))
            return {"lat": lat, "lng": lng}
        return p

    def _to_dict(self, order: Order) -> dict:
        return {
            "user_id": order.user_id,
            "pickup_point": order.pickup_point,
            "pickup_address": order.pickup_address,
            "pickup_area_code": order.pickup_area_code,
            "pickup_location": self._point_to_db(order.pickup_location),
            "pickup_phone": order.pickup_phone,
            "pickup_note": order.pickup_note,
            "status": order.status.value if isinstance(order.status, OrderStatus) else order.status,
            "order_type": order.order_type.value if isinstance(order.order_type, OrderType) else order.order_type
        }

    def _from_dict(self, data: dict) -> Order:
        return Order(
            id=data.get("id"),
            user_id=data.get("user_id"),
            pickup_point=data.get("pickup_point"),
            pickup_address=data.get("pickup_address"),
            pickup_area_code=data.get("pickup_area_code"),
            pickup_location=self._point_from_db(data.get("pickup_location")),
            pickup_phone=data.get("pickup_phone"),
            pickup_note=data.get("pickup_note"),
            status=OrderStatus(data.get("status")),
            order_type=OrderType(data.get("order_type")),
            created_at=datetime.fromisoformat(data.get("created_at").replace('Z', '+00:00'))
            if data.get("created_at") else None,
            order_details=[]
        )

    async def create(self, order: Order) -> Order:
        data = self._to_dict(order)
        response = self._table().insert(data).execute()

        if not response.data:
            raise Exception("Không thể tạo đơn hàng")

        return self._from_dict(response.data[0])

    async def get_by_id(self, order_id: str) -> Optional[Order]:
        response = (
            self._table()
            .select("*")
            .eq("id", order_id)
            .execute()
        )

        if not response.data:
            return None

        return self._from_dict(response.data[0])

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        response = (
            self._table()
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        return [self._from_dict(item) for item in response.data]

    async def update_status(self, order_id: str, status: str) -> bool:
        response = (
            self._table()
            .update({"status": status})
            .eq("id", order_id)
            .execute()
        )

        return len(response.data) > 0

    async def update(self, order: Order) -> Order:
        data = self._to_dict(order)

        response = (
            self._table()
            .update(data)
            .eq("id", order.id)
            .execute()
        )

        if not response.data:
            raise Exception("Không thể cập nhật đơn hàng")

        return self._from_dict(response.data[0])
