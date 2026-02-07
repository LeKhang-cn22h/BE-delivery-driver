from typing import List, Optional
from datetime import datetime

from infrastructure.database.supabase_client import SupabaseClient
from domain.repositories.order_repository import OrderRepository
from domain.entities.order import Order, OrderStatus, OrderType, PickupStatus


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
            "post_office_id": order.post_office_id,
            "pickup_point": order.pickup_point,
            "pickup_address": order.pickup_address,
            "pickup_area_code": order.pickup_area_code,
            "pickup_location": self._point_to_db(order.pickup_location),
            "pickup_phone": order.pickup_phone,
            "pickup_note": order.pickup_note,
            "status": order.status.value if isinstance(order.status, OrderStatus) else order.status,
            "pickup_status": order.pickup_status.value if isinstance(order.pickup_status,
                                                                     PickupStatus) else order.pickup_status,
            "order_type": order.order_type.value if isinstance(order.order_type, OrderType) else order.order_type
        }

    def _from_dict(self, data: dict) -> Order:
        details_data = data.get("order_details", [])
        if isinstance(details_data, list) and len(details_data) > 0:
            total_packages = details_data[0].get("count", 0)
        else:
            total_packages = 0
        return Order(
            id=data.get("id"),
            user_id=data.get("user_id"),
            post_office_id=data.get("post_office_id"),
            pickup_point=data.get("pickup_point"),
            pickup_address=data.get("pickup_address"),
            pickup_area_code=data.get("pickup_area_code"),
            pickup_location=self._point_from_db(data.get("pickup_location")),
            pickup_phone=data.get("pickup_phone"),
            pickup_note=data.get("pickup_note"),
            status=OrderStatus(data.get("status")),
            pickup_status=PickupStatus(data.get("pickup_status")) if data.get("pickup_status") else None,
            order_type=OrderType(data.get("order_type")),
            created_at=datetime.fromisoformat(data.get("created_at").replace('Z', '+00:00'))
            if data.get("created_at") else None,
            order_details=[],
            _total_packages=total_packages
        )

    # =========================================================================
    # DYNAMIC QUERY - thay thế tất cả các method get_by_xxx riêng lẻ
    # =========================================================================
    async def query_orders(
        self,
        post_office_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        pickup_status: Optional[str] = None,
        order_type: Optional[str] = None,
        pickup_area_code: Optional[str] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> List[Order]:
        """
        Dynamic query - 1 method xử lý tất cả tổ hợp filter.
        Chỉ apply filter khi param không None.
        """
        query = self._table().select("*, order_details(count)")

        # Apply filters dynamically
        filters = {
            "post_office_id": post_office_id,
            "user_id": user_id,
            "status": status,
            "pickup_status": pickup_status,
            "order_type": order_type,
            "pickup_area_code": pickup_area_code,
        }

        for column, value in filters.items():
            if value is not None:
                query = query.eq(column, value)

        response = (
            query
            .order("created_at", desc=True)
            .range(skip, skip + limit - 1)
            .execute()
        )

        return [self._from_dict(item) for item in response.data]

    # =========================================================================
    # Giữ lại các method CRUD cơ bản
    # =========================================================================
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

    async def get_by_postid(self, post_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy danh sách đơn hàng của post office"""
        return await self.query_orders(post_office_id=post_id, skip=skip, limit=limit)

    async def get_by_post_status(self, post_id: str, status: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy danh sách đơn hàng của post office theo status"""
        return await self.query_orders(post_office_id=post_id, status=status, skip=skip, limit=limit)

    async def get_by_pickupStatus(self, post_id: str, pickup_status: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy danh sách đơn hàng theo post office và pickup_status"""
        return await self.query_orders(post_office_id=post_id, pickup_status=pickup_status, skip=skip, limit=limit)

    async def get_by_pickupStatus_status(self, post_id: str, status: str, pickup_status: str, skip: int = 0, limit: int = 10) -> List[Order]:
        """Lấy danh sách đơn hàng theo post office, status và pickup_status"""
        return await self.query_orders(
            post_office_id=post_id, 
            status=status, 
            pickup_status=pickup_status, 
            skip=skip, 
            limit=limit
        )

    # =========================================================================
    # Backward-compatible wrappers (có thể xóa dần)
    # =========================================================================
    async def get_by_post(self, post_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        return await self.query_orders(post_office_id=post_id, skip=skip, limit=limit)

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 10) -> List[Order]:
        return await self.query_orders(user_id=user_id, skip=skip, limit=limit)