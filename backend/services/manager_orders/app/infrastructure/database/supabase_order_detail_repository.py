# app/infrastructure/repositories/supabase_order_detail_repository.py
from typing import List
from domain.repositories.order_detail_repository import OrderDetailRepository
from domain.entities.order import OrderDetail, DetailStatus
from infrastructure.database import SupabaseClient


class SupabaseOrderDetailRepository(OrderDetailRepository):
    def __init__(self):
        self.client = SupabaseClient.get_client()
        self.schema = "delivery"
        self.table_name = "order_details"

    def _table(self):
        return self.client.schema(self.schema).table(self.table_name)

    def _point_to_db(self, p):
        if p is None:
            return None
        # Postgres POINT: (x,y) = (lng,lat)
        return f"({p.lng},{p.lat})"

    def _point_from_db(self, p):
        if p is None:
            return None
        if isinstance(p, dict):
            return p  # nếu supabase trả dạng dict (1 số config)
        if isinstance(p, str):
            p = p.strip("()")
            lng, lat = map(float, p.split(","))
            return {"lat": lat, "lng": lng}
        return None

    def _to_dict(self, detail: OrderDetail) -> dict:
        return {
            "order_id": detail.order_id,
            "start_point": detail.start_point,
            "address_detail": detail.address_detail,
            "area_code": detail.area_code,
            "location": self._point_to_db(detail.location),
            "status": detail.status.value if isinstance(detail.status, DetailStatus) else detail.status,
            "priority_score": detail.priority_score,
            "note_send":detail.note_send,
            "recipient_id":detail.recipient_id

        }

    def _from_dict(self, data: dict) -> OrderDetail:
        return OrderDetail(
            id=data.get("id"),
            order_id=data.get("order_id"),
            start_point=data.get("start_point"),
            address_detail=data.get("address_detail"),
            area_code=data.get("area_code"),
            location=self._point_from_db(data.get("location")),
            status=DetailStatus(data.get("status")),
            priority_score=data.get("priority_score", 0),
            note_send=data.get("note_send"),
            recipient_id=data.get("recipient_id")
        )

    async def create_batch(self, order_details: List[OrderDetail]) -> List[OrderDetail]:
        data_list = [self._to_dict(detail) for detail in order_details]

        response = self._table().insert(data_list).execute()

        if not response.data:
            raise Exception("Không thể tạo chi tiết đơn hàng")

        return [self._from_dict(item) for item in response.data]

    async def get_by_order_id(self, order_id: str) -> List[OrderDetail]:
        response = (
            self._table()
            .select("*")
            .eq("order_id", order_id)
            .order("priority_score", desc=True)
            .execute()
        )

        return [self._from_dict(item) for item in response.data]

    async def update_detail_status(self, detail_id: str, status: str) -> bool:
        response = (
            self._table()
            .update({"status": status})
            .eq("id", detail_id)
            .execute()
        )

        return len(response.data) > 0
