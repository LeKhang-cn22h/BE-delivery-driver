from typing import List
from uuid import UUID
from datetime import date
import asyncio
from functools import wraps


def async_wrap(func):
    """Decorator để wrap synchronous Supabase calls thành async"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    return wrapper


class DriverSchedulingRepository:
    def __init__(self, supabase_client):
        self.db = supabase_client

    def get_table(self, table_name: str):
        """Helper để gọi bảng từ schema delivery"""
        return self.db.schema("delivery").table(table_name)

    # 1. Lấy tài xế available
    async def get_available_drivers(self, post_office_id: UUID, scheduled_date: date) -> List[dict]:
        """Lấy danh sách tài xế available cho bưu cục"""
        # Chạy trong thread pool để không block
        loop = asyncio.get_event_loop()

        def _get_drivers():
            drivers = (
                self.get_table("drivers")
                .select("id, name, phone, status, post_office_id")
                .eq("post_office_id", str(post_office_id))
                .in_("status", ["available", "busy"])
                .execute()
            ).data

            if not drivers:
                return []

            # Lọc bỏ tài xế đã có schedule hôm đó
            result = []
            for d in drivers:
                schedules = (
                    self.get_table("schedules")
                    .select("id")
                    .eq("driver_id", d["id"])
                    .eq("scheduled_date", str(scheduled_date))
                    .in_("status", ["confirmed", "in_progress"])
                    .execute()
                ).data

                if not schedules:
                    # Lấy thêm location từ driver_current_locations nếu có
                    location_data = (
                        self.get_table("driver_current_locations")
                        .select("location, status")
                        .eq("driver_id", d["id"])
                        .execute()
                    ).data

                    if location_data:
                        d["location"] = location_data[0].get("location")
                        d["current_status"] = location_data[0].get("status")
                    else:
                        d["location"] = None
                        d["current_status"] = None

                    result.append(d)

            return result

        return await loop.run_in_executor(None, _get_drivers)

    # 2. Lấy orders pending
    async def get_pending_orders_by_area(self, area_codes: List[str], post_office_id: UUID) -> List[dict]:
        """Lấy các đơn hàng pending theo area_code"""
        loop = asyncio.get_event_loop()

        def _get_orders():
            orders = (
                self.get_table("order_details")
                .select("id, order_id, start_point, address_detail, area_code, location, priority_score")
                .in_("area_code", area_codes)
                .eq("status", "pending")
                .execute()
            ).data

            if not orders:
                return []

            # Filter theo post_office + chưa có schedule
            result = []
            for od in orders:
                # Lấy thông tin order
                order = (
                    self.get_table("orders")
                    .select("id, post_office_id, status, pickup_location, pickup_point")
                    .eq("id", od["order_id"])
                    .execute()
                ).data

                if not order or len(order) == 0:
                    continue

                order = order[0]

                # Check post_office
                if order["post_office_id"] != str(post_office_id):
                    continue

                # Check status
                if order["status"] not in ["confirmed", "processing"]:
                    continue

                # Check chưa có schedule
                schedule_items = (
                    self.get_table("schedule_items")
                    .select("id, schedule_id")
                    .eq("order_detail_id", od["id"])
                    .execute()
                ).data

                if schedule_items and len(schedule_items) > 0:
                    # Kiểm tra xem schedule_items này có thuộc schedule đang active không
                    has_active_schedule = False
                    for si in schedule_items:
                        schedule = (
                            self.get_table("schedules")
                            .select("status")
                            .eq("id", si.get("schedule_id"))
                            .in_("status", ["draft", "confirmed", "in_progress"])
                            .execute()
                        ).data

                        if schedule and len(schedule) > 0:
                            has_active_schedule = True
                            break

                    if has_active_schedule:
                        continue

                # Thêm thông tin pickup vào order_detail
                od["pickup_location"] = order.get("pickup_location")
                od["pickup_point"] = order.get("pickup_point")

                result.append(od)

            return result

        return await loop.run_in_executor(None, _get_orders)

    # 3. Tạo schedule
    async def create_schedule(self, driver_id: UUID, scheduled_date: date, area_code: str,
                              post_office_id: UUID) -> UUID:
        """Tạo schedule mới"""
        loop = asyncio.get_event_loop()

        def _create():
            res = (
                self.get_table("schedules")
                .insert({
                    "driver_id": str(driver_id),
                    "scheduled_date": str(scheduled_date),
                    "area_code": area_code,
                    "status": "draft",
                    "post_office_id": str(post_office_id),
                    "total_orders": 0,
                    "completed_orders": 0,
                    "failed_orders": 0
                })
                .execute()
            )
            return UUID(res.data[0]["id"])

        return await loop.run_in_executor(None, _create)

    # 4. Tạo schedule items
    async def create_schedule_items(self, schedule_id: UUID, order_detail_ids: List[UUID],
                                    route_sequence: List[int]) -> None:
        """Tạo các schedule items theo thứ tự route"""
        loop = asyncio.get_event_loop()

        def _create_items():
            rows = []
            for i, order_id in enumerate(order_detail_ids):
                queue = route_sequence[i] if i < len(route_sequence) else i + 1
                rows.append({
                    "schedule_id": str(schedule_id),
                    "order_detail_id": str(order_id),
                    "status": "pending",
                    "queue": queue
                })

            self.get_table("schedule_items").insert(rows).execute()

            # Update total_orders
            self.get_table("schedules").update({
                "total_orders": len(order_detail_ids)
            }).eq("id", str(schedule_id)).execute()

        await loop.run_in_executor(None, _create_items)

    # 5. Update schedule status
    async def update_schedule_status(self, schedule_id: UUID, status: str) -> None:
        """Cập nhật trạng thái schedule"""
        loop = asyncio.get_event_loop()

        def _update():
            self.get_table("schedules").update({
                "status": status
            }).eq("id", str(schedule_id)).execute()

        await loop.run_in_executor(None, _update)

    # 6. Update driver status
    async def update_driver_status(self, driver_id: UUID, status: str) -> None:
        """Cập nhật trạng thái tài xế"""
        loop = asyncio.get_event_loop()

        def _update():
            self.get_table("drivers").update({
                "status": status
            }).eq("id", str(driver_id)).execute()

        await loop.run_in_executor(None, _update)