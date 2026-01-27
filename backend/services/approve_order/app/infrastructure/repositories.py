from typing import List, Optional
from datetime import datetime
from supabase import Client

from domain.models import OrderDetail, Schedule, ScheduleItem
from domain.Repositories import (
    IOrderRepository,
    IScheduleRepository,
    IScheduleItemRepository
)


class OrderRepository(IOrderRepository):
    """Implementation của Order Repository với Supabase"""

    def __init__(self, supabase_client: Client, schema: str = "delivery"):
        self.db = supabase_client
        self.schema = schema

    async def get_pending_order_details(self, post_office_id: str) -> List[OrderDetail]:
        """Lấy tất cả order details có status = 'pending'"""
        try:
            response = (
                self.db.schema(self.schema)  # Thêm schema
                .table("order_details")
                .select("""
                    id,
                    order_id,
                    start_point,
                    price,
                    status,
                    address_detail,
                    area_code,
                    location,
                    priority_score,
                    orders!inner(post_office_id)
                """)
                .eq("status", "pending")
                .eq("orders.post_office_id", post_office_id)
                .execute()
            )

            return [OrderDetail(**item) for item in response.data]
        except Exception as e:
            raise Exception(f"Lỗi khi lấy pending orders: {str(e)}")

    async def get_order_details_by_area(
            self,
            post_office_id: str,
            area_code: str
    ) -> List[OrderDetail]:
        """Lấy order details theo area_code"""
        try:
            response = (
                self.db.schema(self.schema)  # Thêm schema
                .table("order_details")
                .select("""
                    id,
                    order_id,
                    start_point,
                    price,
                    status,
                    address_detail,
                    area_code,
                    location,
                    priority_score,
                    orders!inner(post_office_id)
                """)
                .eq("status", "pending")
                .eq("area_code", area_code)
                .eq("orders.post_office_id", post_office_id)
                .execute()
            )

            return [OrderDetail(**item) for item in response.data]
        except Exception as e:
            raise Exception(f"Lỗi khi lấy orders theo vùng: {str(e)}")

    async def update_order_detail_status(
            self,
            order_detail_id: str,
            status: str
    ) -> bool:
        """Cập nhật status của order detail"""
        try:
            response = (
                self.db.schema(self.schema)  # Thêm schema
                .table("order_details")
                .update({"status": status})
                .eq("id", order_detail_id)
                .execute()
            )
            return len(response.data) > 0
        except Exception as e:
            raise Exception(f"Lỗi khi cập nhật status: {str(e)}")


class ScheduleRepository(IScheduleRepository):
    """Implementation của Schedule Repository với Supabase"""

    def __init__(self, supabase_client: Client, schema: str = "delivery"):
        self.db = supabase_client
        self.schema = schema

    async def create_schedule(self, schedule_data: dict) -> Schedule:
        """Tạo schedule mới"""
        try:
            response = (
                self.db.schema(self.schema)  # Thêm schema
                .table("schedules")
                .insert(schedule_data)
                .execute()
            )

            if not response.data:
                raise Exception("Không thể tạo schedule")

            return Schedule(**response.data[0])
        except Exception as e:
            raise Exception(f"Lỗi khi tạo schedule: {str(e)}")

    async def get_schedule_by_id(self, schedule_id: str) -> Optional[Schedule]:
        """Lấy schedule theo ID"""
        try:
            response = (
                self.db.schema(self.schema)  # Thêm schema
                .table("schedules")
                .select("*")
                .eq("id", schedule_id)
                .execute()
            )

            if not response.data:
                return None

            return Schedule(**response.data[0])
        except Exception as e:
            raise Exception(f"Lỗi khi lấy schedule: {str(e)}")

    async def update_schedule(
            self,
            schedule_id: str,
            update_data: dict
    ) -> Schedule:
        """Cập nhật thông tin schedule"""
        try:
            response = (
                self.db.schema(self.schema)  # Thêm schema
                .table("schedules")
                .update(update_data)
                .eq("id", schedule_id)
                .execute()
            )

            if not response.data:
                raise Exception("Không thể cập nhật schedule")

            return Schedule(**response.data[0])
        except Exception as e:
            raise Exception(f"Lỗi khi cập nhật schedule: {str(e)}")

    async def get_schedules_by_date_and_area(
            self,
            post_office_id: str,
            scheduled_date: datetime,
            area_code: str
    ) -> Optional[Schedule]:
        """Kiểm tra xem đã có schedule cho ngày và vùng này chưa"""
        try:
            date_str = scheduled_date.date().isoformat()

            response = (
                self.db.schema(self.schema)  # Thêm schema
                .table("schedules")
                .select("*")
                .eq("post_office_id", post_office_id)
                .eq("area_code", area_code)
                .gte("scheduled_date", f"{date_str}T00:00:00")
                .lt("scheduled_date", f"{date_str}T23:59:59")
                .execute()
            )

            if not response.data:
                return None

            return Schedule(**response.data[0])
        except Exception as e:
            raise Exception(f"Lỗi khi tìm schedule: {str(e)}")


class ScheduleItemRepository(IScheduleItemRepository):
    """Implementation của Schedule Item Repository với Supabase"""

    def __init__(self, supabase_client: Client, schema: str = "delivery"):
        self.db = supabase_client
        self.schema = schema

    async def create_schedule_item(self, item_data: dict) -> ScheduleItem:
        """Tạo schedule item mới"""
        try:
            response = (
                self.db.schema(self.schema)  # Thêm schema
                .table("schedule_items")
                .insert(item_data)
                .execute()
            )

            if not response.data:
                raise Exception("Không thể tạo schedule item")

            return ScheduleItem(**response.data[0])
        except Exception as e:
            raise Exception(f"Lỗi khi tạo schedule item: {str(e)}")

    async def create_schedule_items_batch(
            self,
            items_data: List[dict]
    ) -> List[ScheduleItem]:
        """Tạo nhiều schedule items cùng lúc"""
        try:
            response = (
                self.db.schema(self.schema)  # Thêm schema
                .table("schedule_items")
                .insert(items_data)
                .execute()
            )

            if not response.data:
                raise Exception("Không thể tạo schedule items")

            return [ScheduleItem(**item) for item in response.data]
        except Exception as e:
            raise Exception(f"Lỗi khi tạo batch schedule items: {str(e)}")

    async def get_items_by_schedule(
            self,
            schedule_id: str
    ) -> List[ScheduleItem]:
        """Lấy tất cả items của một schedule"""
        try:
            response = (
                self.db.schema(self.schema)  # Thêm schema
                .table("schedule_items")
                .select("*")
                .eq("schedule_id", schedule_id)
                .order("queue")
                .execute()
            )

            return [ScheduleItem(**item) for item in response.data]
        except Exception as e:
            raise Exception(f"Lỗi khi lấy schedule items: {str(e)}")

    async def get_max_queue_number(self, schedule_id: str) -> int:
        """Lấy số queue lớn nhất trong schedule"""
        try:
            response = (
                self.db.schema(self.schema)  # Thêm schema
                .table("schedule_items")
                .select("queue")
                .eq("schedule_id", schedule_id)
                .order("queue", desc=True)
                .limit(1)
                .execute()
            )

            if not response.data:
                return 0

            return response.data[0]["queue"]
        except Exception as e:
            return 0