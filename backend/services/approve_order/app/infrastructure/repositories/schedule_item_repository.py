from typing import List
from uuid import uuid4
from datetime import datetime
from supabase import Client
from domain.models import ScheduleItem, OrderDetail


class ScheduleItemRepository:
    """Repository cho Schedule Item với Supabase"""

    def __init__(self, supabase_client: Client, schema: str = "public"):
        self.db = supabase_client
        self.schema = schema

    async def create_schedule_items(
            self,
            schedule_id: str,
            order_details: List[OrderDetail]
    ) -> List[ScheduleItem]:
        """Tạo nhiều schedule items với queue number"""
        try:
            items_data = []

            for idx, order_detail in enumerate(order_details, start=1):
                item = {
                    "id": str(uuid4()),
                    "schedule_id": schedule_id,
                    "order_detail_id": order_detail.id,
                    "status": "pending",
                    "queue": idx,
                    "created_at": datetime.now().isoformat()
                }
                items_data.append(item)

            response = (
                self.db.schema(self.schema)
                .table("schedule_items")
                .insert(items_data)
                .execute()
            )

            if not response.data:
                raise Exception("Không thể tạo schedule items")

            return [ScheduleItem(**item) for item in response.data]

        except Exception as e:
            raise Exception(f"Lỗi khi tạo schedule items: {str(e)}")

    async def get_items_by_schedule(
            self,
            schedule_id: str
    ) -> List[ScheduleItem]:
        """Lấy tất cả items của một schedule"""
        try:
            response = (
                self.db.schema(self.schema)
                .table("schedule_items")
                .select("""
                    *,
                    order_details!inner(
                        start_point,
                        price,
                        address_detail
                    )
                """)
                .eq("schedule_id", schedule_id)
                .order("queue", desc=False)
                .execute()
            )

            return [ScheduleItem(**item) for item in response.data]

        except Exception as e:
            raise Exception(f"Lỗi khi lấy schedule items: {str(e)}")