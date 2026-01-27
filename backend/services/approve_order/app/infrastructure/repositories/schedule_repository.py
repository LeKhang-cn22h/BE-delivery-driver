from typing import Optional
from datetime import datetime
from uuid import uuid4
from supabase import Client
from domain.models import Schedule


class ScheduleRepository:
    """Repository cho Schedule với Supabase"""

    def __init__(self, supabase_client: Client, schema: str = "public"):
        self.db = supabase_client
        self.schema = schema

    async def create_schedule(
            self,
            post_office_id: str,
            area_code: str,
            scheduled_date: datetime,
            total_orders: int
    ) -> Schedule:
        """Tạo schedule mới"""
        try:
            schedule_data = {
                "id": str(uuid4()),
                "post_office_id": post_office_id,
                "area_code": area_code,
                "scheduled_date": scheduled_date.isoformat(),
                "status": "pending",
                "total_orders": total_orders,
                "completed_orders": 0,
                "failed_orders": 0,
                "created_at": datetime.now().isoformat()
            }

            response = (
                self.db.schema(self.schema)
                .table("schedules")
                .insert(schedule_data)
                .execute()
            )

            if not response.data:
                raise Exception("Không thể tạo schedule")

            return Schedule(**response.data[0])

        except Exception as e:
            raise Exception(f"Lỗi khi tạo schedule: {str(e)}")

    async def get_by_id(self, schedule_id: str) -> Optional[Schedule]:
        """Lấy schedule theo ID"""
        try:
            response = (
                self.db.schema(self.schema)
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