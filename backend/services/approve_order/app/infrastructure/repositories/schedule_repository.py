# infrastructure/repositories/schedule_repository.py
from typing import Optional
from uuid import uuid4
from datetime import datetime
from supabase import Client
from domain.models import Schedule


class ScheduleRepository:
    """Repository cho Schedule với Supabase"""

    def __init__(self, supabase_client: Client, schema: str = "delivery"):
        self.db = supabase_client
        self.schema = schema

    async def create_schedule(
            self,
            post_office_id: str,
            area_code: str,
            scheduled_date: datetime,
            total_orders: int,
            status: str = 'draft',  # ✅ THÊM parameter status với default 'draft'
            driver_id: Optional[str] = None
    ) -> Schedule:
        """
        Tạo schedule mới cho một vùng

        Valid statuses: 'draft', 'confirmed', 'in_progress', 'completed'
        Status mặc định: 'draft'
        """
        try:
            schedule_data = {
                "id": str(uuid4()),
                "driver_id": driver_id,
                "scheduled_date": scheduled_date.date().isoformat() if isinstance(scheduled_date, datetime) else scheduled_date.isoformat(),
                "area_code": area_code,
                "status": status,  # ✅ SỬA: Dùng parameter status thay vì hardcode
                "total_orders": total_orders,
                "completed_orders": 0,
                "failed_orders": 0,
                "created_at": datetime.now().isoformat(),
                "post_office_id": post_office_id
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

    async def get_schedule_by_id(self, schedule_id: str) -> Schedule:
        """Lấy schedule theo ID"""
        try:
            response = (
                self.db.schema(self.schema)
                .table("schedules")
                .select("*")
                .eq("id", schedule_id)
                .single()
                .execute()
            )

            return Schedule(**response.data)

        except Exception as e:
            raise Exception(f"Lỗi khi lấy schedule: {str(e)}")

    async def update_schedule_status(
            self,
            schedule_id: str,
            status: str
    ) -> Schedule:
        """
        Cập nhật status của schedule

        Valid statuses: 'draft', 'confirmed', 'in_progress', 'completed'
        """
        try:
            response = (
                self.db.schema(self.schema)
                .table("schedules")
                .update({"status": status})
                .eq("id", schedule_id)
                .execute()
            )

            if not response.data:
                raise Exception("Không thể cập nhật schedule")

            return Schedule(**response.data[0])

        except Exception as e:
            raise Exception(f"Lỗi khi cập nhật schedule: {str(e)}")

    async def update_schedule_progress(
            self,
            schedule_id: str,
            completed_orders: int,
            failed_orders: int
    ) -> Schedule:
        """Cập nhật tiến độ của schedule"""
        try:
            response = (
                self.db.schema(self.schema)
                .table("schedules")
                .update({
                    "completed_orders": completed_orders,
                    "failed_orders": failed_orders
                })
                .eq("id", schedule_id)
                .execute()
            )

            if not response.data:
                raise Exception("Không thể cập nhật tiến độ")

            return Schedule(**response.data[0])

        except Exception as e:
            raise Exception(f"Lỗi khi cập nhật tiến độ: {str(e)}")

    async def assign_driver(
            self,
            schedule_id: str,
            driver_id: str
    ) -> Schedule:
        """Gán tài xế cho schedule"""
        try:
            response = (
                self.db.schema(self.schema)
                .table("schedules")
                .update({"driver_id": driver_id})
                .eq("id", schedule_id)
                .execute()
            )

            if not response.data:
                raise Exception("Không thể gán tài xế")

            return Schedule(**response.data[0])

        except Exception as e:
            raise Exception(f"Lỗi khi gán tài xế: {str(e)}")