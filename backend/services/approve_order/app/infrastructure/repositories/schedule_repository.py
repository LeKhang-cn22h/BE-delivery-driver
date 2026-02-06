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
        
    async def update_schedule_fields(self, schedule_id: str, update_data: dict):
        """Update specific fields of a schedule"""
        try:
            response = (
                self.db
                .schema(self.schema)
                .table("schedules")
                .update(update_data)
                .eq("id", schedule_id)
                .execute()
            )
            
            if not response.data or len(response.data) == 0:
                return None
            
            from domain.models import Schedule
            return Schedule(**response.data[0])
        except Exception as e:
            print(f" Error updating schedule: {str(e)}")
            raise