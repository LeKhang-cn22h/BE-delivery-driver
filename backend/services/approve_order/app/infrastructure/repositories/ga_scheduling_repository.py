# infrastructure/repositories/ga_scheduling_repository.py
from typing import List
from uuid import UUID, uuid4
from datetime import date
import asyncio


class GASchedulingRepository:
    """Repository hỗ trợ GA Scheduling Service"""

    def __init__(self, supabase_client):
        self.db = supabase_client
        self.schema = "delivery"

    def _get_table(self, table_name: str):
        """Helper để gọi bảng từ schema delivery"""
        return self.db.schema(self.schema).table(table_name)

    async def get_pending_orders(
        self, 
        area_codes: List[str], 
        post_office_id: UUID
    ) -> List[dict]:
        """
        Lấy đơn hàng pending theo area_codes và post_office_id
        Chỉ lấy đơn chưa có trong schedule active
        """
        loop = asyncio.get_event_loop()

        def _query():
            # 1. Lấy order_details theo area_code và status pending
            order_details = (
                self._get_table("order_details")
                .select("id, order_id, start_point, address_detail, area_code, location, priority_score, status")
                .in_("area_code", area_codes)
                .eq("status", "confirmed")
                .execute()
            ).data

            if not order_details:
                return []

            # 2. Filter theo post_office và chưa có schedule active
            result = []
            for od in order_details:
                # Check order thuộc post_office
                order = (
                    self._get_table("orders")
                    .select("id, post_office_id, status, pickup_location, pickup_point")
                    .eq("id", od["order_id"])
                    .execute()
                ).data

                if not order:
                    continue

                order = order[0]

                # Check post_office_id
                if order["post_office_id"] != str(post_office_id):
                    continue

                # Check order status
                if order["status"] not in ["confirmed", "processing"]:
                    continue

                # Check chưa có schedule active
                schedule_items = (
                    self._get_table("schedule_items")
                    .select("id, schedule_id")
                    .eq("order_detail_id", od["id"])
                    .execute()
                ).data

                has_active_schedule = False
                if schedule_items:
                    for si in schedule_items:
                        schedule = (
                            self._get_table("schedules")
                            .select("status")
                            .eq("id", si["schedule_id"])
                            .in_("status", ["draft", "confirmed", "in_progress"])
                            .execute()
                        ).data

                        if schedule:
                            has_active_schedule = True
                            break

                if has_active_schedule:
                    continue

                # Thêm pickup info
                od["pickup_location"] = order.get("pickup_location")
                od["pickup_point"] = order.get("pickup_point")
                result.append(od)

            return result

        return await loop.run_in_executor(None, _query)

    async def create_schedule(
        self,
        scheduled_date: date,
        area_code: str,
        post_office_id: UUID,
        total_orders: int
    ) -> UUID:
        """Tạo schedule mới (KHÔNG có driver)"""
        loop = asyncio.get_event_loop()

        def _create():
            schedule_id = str(uuid4())
            
            data = {
                "id": schedule_id,
                "driver_id": None,  # Chưa gán driver
                "scheduled_date": str(scheduled_date),
                "area_code": area_code,
                "status": "draft",
                "post_office_id": str(post_office_id),
                "total_orders": total_orders,
                "completed_orders": 0,
                "failed_orders": 0
            }

            self._get_table("schedules").insert(data).execute()
            return UUID(schedule_id)

        return await loop.run_in_executor(None, _create)

    async def create_schedule_items(
        self,
        schedule_id: UUID,
        order_detail_ids: List[str]
    ) -> None:
        """Tạo schedule items theo thứ tự"""
        loop = asyncio.get_event_loop()

        def _create():
            rows = []
            for idx, od_id in enumerate(order_detail_ids):
                rows.append({
                    "id": str(uuid4()),
                    "schedule_id": str(schedule_id),
                    "order_detail_id": od_id,
                    "status": "pending",
                    "queue": idx + 1
                })

            if rows:
                self._get_table("schedule_items").insert(rows).execute()

        await loop.run_in_executor(None, _create)

    async def update_order_details_status(
        self,
        order_detail_ids: List[str],
        status: str
    ) -> None:
        """Cập nhật status của các order_details"""
        loop = asyncio.get_event_loop()

        def _update():
            self._get_table("order_details").update({
                "status": status
            }).in_("id", order_detail_ids).execute()

        await loop.run_in_executor(None, _update)
