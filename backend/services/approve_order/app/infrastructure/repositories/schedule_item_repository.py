# infrastructure/repositories/schedule_item_repository.py
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from supabase import Client
from domain.models import ScheduleItem, OrderDetail


class ScheduleItemRepository:
    """Repository cho Schedule Item với Supabase"""

    def __init__(self, supabase_client: Client, schema: str = "delivery"):
        self.db = supabase_client
        self.schema = schema

    async def create_schedule_items(
            self,
            schedule_id: str,
            order_details: List[OrderDetail]
    ) -> List[ScheduleItem]:
        """
        Tạo nhiều schedule items với queue number theo priority_score
        order_details phải đã được sắp xếp theo priority_score giảm dần
        """
        try:
            items_data = []

            # Sắp xếp lại theo priority_score để đảm bảo
            sorted_orders = sorted(
                order_details,
                key=lambda x: x.priority_score if x.priority_score else 0,
                reverse=True
            )

            for idx, order_detail in enumerate(sorted_orders, start=1):
                item = {
                    "id": str(uuid4()),
                    "schedule_id": schedule_id,
                    "order_detail_id": order_detail.id,
                    "status": "pending",
                    "queue": idx,  # ✅ SỬA: Đổi từ 'queue_number' sang 'queue'
                    # ✅ XÓA: Không có cột 'created_at'
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
        """Lấy tất cả items của một schedule, sắp xếp theo queue"""
        try:
            response = (
                self.db.schema(self.schema)
                .table("schedule_items")
                .select("""
                    *,
                    order_details!inner(
                        id,
                        start_point,
                        price,
                        address_detail,
                        priority_score,
                        area_code
                    )
                """)
                .eq("schedule_id", schedule_id)
                .order("queue", desc=False)  # ✅ SỬA: Đổi từ 'queue_number' sang 'queue'
                .execute()
            )

            return [ScheduleItem(**item) for item in response.data]

        except Exception as e:
            raise Exception(f"Lỗi khi lấy schedule items: {str(e)}")

    async def get_max_queue_number(self, schedule_id: str) -> int:
        """Lấy queue number lớn nhất trong schedule"""
        try:
            response = (
                self.db.schema(self.schema)
                .table("schedule_items")
                .select("queue")  # ✅ SỬA: Đổi từ 'queue_number' sang 'queue'
                .eq("schedule_id", schedule_id)
                .order("queue", desc=True)  # ✅ SỬA
                .limit(1)
                .execute()
            )

            if not response.data:
                return 0

            return response.data[0]["queue"]  # ✅ SỬA

        except Exception as e:
            raise Exception(f"Lỗi khi lấy max queue: {str(e)}")

    async def update_item_status(
            self,
            item_id: str,
            status: str,
            delivered_at: Optional[datetime] = None,
            failure_reason: Optional[str] = None
    ) -> ScheduleItem:
        """Cập nhật status của schedule item"""
        try:
            update_data = {"status": status}

            if delivered_at:
                update_data["delivered_at"] = delivered_at.isoformat()

            if failure_reason:
                update_data["failure_reason"] = failure_reason

            response = (
                self.db.schema(self.schema)
                .table("schedule_items")
                .update(update_data)
                .eq("id", item_id)
                .execute()
            )

            if not response.data:
                raise Exception("Không thể cập nhật schedule item")

            return ScheduleItem(**response.data[0])

        except Exception as e:
            raise Exception(f"Lỗi khi cập nhật item: {str(e)}")