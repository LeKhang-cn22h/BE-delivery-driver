"""
Schedule Repository Implementation using Supabase
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from domain.repositories.schedule_repository import (
    IScheduleRepository,
    IDriverRepository,
    IOrderRepository
)
from domain.entities.schedule import Schedule, ScheduleItem
from domain.entities.driver import Driver
from domain.entities.order import OrderDetail, Order
from infrastructure.database.supabase_client import SupabaseClient


class ScheduleRepositoryImpl(IScheduleRepository):
    """Supabase implementation of schedule repository"""

    def __init__(self):
        self.client = SupabaseClient.get_client()

    async def create_schedule(self, schedule: Schedule) -> Schedule:
        """Create new schedule"""
        # Insert schedule
        schedule_data = {
            "id": str(schedule.id),
            "driver_id": str(schedule.driver_id),
            "area_code": schedule.area_code,
            "scheduled_date": schedule.scheduled_date.isoformat(),
            "status": schedule.status,
            "total_orders": schedule.total_orders,
            "completed_orders": schedule.completed_orders,
            "failed_orders": schedule.failed_orders,
            "post_office_id": str(schedule.post_office_id) if schedule.post_office_id else None,
            "created_at": schedule.created_at.isoformat(),
        }

        result = self.client.table("schedules").insert(schedule_data).execute()

        # Insert schedule items
        if schedule.items:
            items_data = [
                {
                    "id": str(item.id),
                    "schedule_id": str(schedule.id),
                    "order_detail_id": str(item.order_detail_id),
                    "status": item.status,
                    "queue": item.queue
                }
                for item in schedule.items
            ]

            self.client.table("schedule_items").insert(items_data).execute()

        return schedule

    async def update_schedule(self, schedule: Schedule) -> Schedule:
        """Update existing schedule"""
        update_data = {
            "status": schedule.status,
            "total_orders": schedule.total_orders,
            "completed_orders": schedule.completed_orders,
            "failed_orders": schedule.failed_orders,
            "updated_at": datetime.now().isoformat()
        }

        self.client.table("schedules").update(update_data).eq(
            "id", str(schedule.id)
        ).execute()

        return schedule

    async def get_schedule_by_id(self, schedule_id: UUID) -> Optional[Schedule]:
        """Get schedule by ID"""
        # Get schedule
        schedule_result = self.client.table("schedules").select("*").eq(
            "id", str(schedule_id)
        ).execute()

        if not schedule_result.data:
            return None

        schedule_data = schedule_result.data[0]

        # Get schedule items
        items_result = self.client.table("schedule_items").select("*").eq(
            "schedule_id", str(schedule_id)
        ).order("queue").execute()

        # Map to domain entities
        schedule = self._map_to_schedule(schedule_data, items_result.data)

        return schedule

    async def get_schedules_by_driver(
            self,
            driver_id: UUID,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Schedule]:
        """Get schedules for a driver"""
        query = self.client.table("schedules").select("*").eq(
            "driver_id", str(driver_id)
        )

        if start_date:
            query = query.gte("scheduled_date", start_date.isoformat())
        if end_date:
            query = query.lte("scheduled_date", end_date.isoformat())

        result = query.execute()

        schedules = []
        for schedule_data in result.data:
            # Get items for each schedule
            items_result = self.client.table("schedule_items").select("*").eq(
                "schedule_id", schedule_data["id"]
            ).order("queue").execute()

            schedule = self._map_to_schedule(schedule_data, items_result.data)
            schedules.append(schedule)

        return schedules

    async def get_schedules_by_date(
            self,
            scheduled_date: datetime,
            post_office_id: Optional[UUID] = None
    ) -> List[Schedule]:
        """Get all schedules for a specific date"""
        query = self.client.table("schedules").select("*").eq(
            "scheduled_date", scheduled_date.date().isoformat()
        )

        if post_office_id:
            query = query.eq("post_office_id", str(post_office_id))

        result = query.execute()

        schedules = []
        for schedule_data in result.data:
            items_result = self.client.table("schedule_items").select("*").eq(
                "schedule_id", schedule_data["id"]
            ).order("queue").execute()

            schedule = self._map_to_schedule(schedule_data, items_result.data)
            schedules.append(schedule)

        return schedules

    async def delete_schedule(self, schedule_id: UUID) -> bool:
        """Delete schedule"""
        # Delete items first (foreign key constraint)
        self.client.table("schedule_items").delete().eq(
            "schedule_id", str(schedule_id)
        ).execute()

        # Delete schedule
        result = self.client.table("schedules").delete().eq(
            "id", str(schedule_id)
        ).execute()

        return len(result.data) > 0

    async def add_schedule_items(
            self,
            schedule_id: UUID,
            items: List[ScheduleItem]
    ) -> List[ScheduleItem]:
        """Add items to schedule"""
        items_data = [
            {
                "id": str(item.id),
                "schedule_id": str(schedule_id),
                "order_detail_id": str(item.order_detail_id),
                "status": item.status,
                "queue": item.queue
            }
            for item in items
        ]

        self.client.table("schedule_items").insert(items_data).execute()

        return items

    def _map_to_schedule(self, schedule_data: dict, items_data: list) -> Schedule:
        """Map database data to Schedule entity"""
        items = [
            ScheduleItem(
                id=UUID(item["id"]),
                schedule_id=UUID(item["schedule_id"]),
                order_detail_id=UUID(item["order_detail_id"]),
                status=item["status"],
                delivered_at=datetime.fromisoformat(item["delivered_at"]) if item.get("delivered_at") else None,
                failure_reason=item.get("failure_reason"),
                queue=item.get("queue")
            )
            for item in items_data
        ]

        schedule = Schedule(
            id=UUID(schedule_data["id"]),
            driver_id=UUID(schedule_data["driver_id"]),
            area_code=schedule_data.get("area_code"),
            scheduled_date=datetime.fromisoformat(schedule_data["scheduled_date"]),
            status=schedule_data["status"],
            total_orders=schedule_data["total_orders"],
            completed_orders=schedule_data["completed_orders"],
            failed_orders=schedule_data["failed_orders"],
            created_at=datetime.fromisoformat(schedule_data["created_at"]),
            updated_at=datetime.fromisoformat(schedule_data["updated_at"]) if schedule_data.get("updated_at") else None,
            post_office_id=UUID(schedule_data["post_office_id"]) if schedule_data.get("post_office_id") else None,
            items=items
        )

        return schedule


class DriverRepositoryImpl(IDriverRepository):
    """Supabase implementation of driver repository"""

    def __init__(self):
        self.client = SupabaseClient.get_client()

    async def get_driver_by_id(self, driver_id: UUID) -> Optional[Driver]:
        """Get driver by ID"""
        result = self.client.table("drivers").select("*").eq(
            "id", str(driver_id)
        ).execute()

        if not result.data:
            return None

        return self._map_to_driver(result.data[0])

    async def get_available_drivers(
            self,
            post_office_id: Optional[UUID] = None,
            area_code: Optional[str] = None
    ) -> List[Driver]:
        """Get available drivers for scheduling"""
        query = self.client.table("drivers").select("*").eq("status", "active")

        if post_office_id:
            query = query.eq("post_office_id", str(post_office_id))

        result = query.execute()

        drivers = [self._map_to_driver(data) for data in result.data]

        # Filter by area if needed
        if area_code:
            # Could check driver's area expertise here
            pass

        return drivers

    async def get_driver_workload(self, driver_id: UUID, date: datetime) -> int:
        """Get number of orders assigned to driver on a date"""
        result = self.client.table("schedules").select("total_orders").eq(
            "driver_id", str(driver_id)
        ).eq("scheduled_date", date.date().isoformat()).execute()

        if not result.data:
            return 0

        return sum(s["total_orders"] for s in result.data)

    def _map_to_driver(self, data: dict) -> Driver:
        """Map database data to Driver entity"""
        return Driver(
            id=UUID(data["id"]),
            user_id=UUID(data["user_id"]),
            name=data["name"],
            phone=data["phone"],
            status=data["status"],
            created_at=datetime.fromisoformat(data["created_at"]),
            post_office_id=UUID(data["post_office_id"])
        )


class OrderRepositoryImpl(IOrderRepository):
    """Supabase implementation of order repository"""

    def __init__(self):
        self.client = SupabaseClient.get_client()

    async def get_pending_orders(
            self,
            post_office_id: Optional[UUID] = None,
            area_code: Optional[str] = None,
            limit: Optional[int] = None
    ) -> List[OrderDetail]:
        """Get pending orders that need scheduling"""
        query = self.client.table("order_details").select(
            "*, orders!inner(*)"
        ).eq("status", "pending")

        if post_office_id:
            query = query.eq("orders.post_office_id", str(post_office_id))

        if area_code:
            query = query.eq("area_code", area_code)

        if limit:
            query = query.limit(limit)

        result = query.execute()

        return [self._map_to_order_detail(data) for data in result.data]

    async def get_order_by_id(self, order_detail_id: UUID) -> Optional[OrderDetail]:
        """Get order detail by ID"""
        result = self.client.table("order_details").select(
            "*, orders(*)"
        ).eq("id", str(order_detail_id)).execute()

        if not result.data:
            return None

        return self._map_to_order_detail(result.data[0])

    async def update_order_status(
            self,
            order_detail_id: UUID,
            status: str
    ) -> bool:
        """Update order status"""
        result = self.client.table("order_details").update({
            "status": status
        }).eq("id", str(order_detail_id)).execute()

        return len(result.data) > 0

    async def get_orders_by_ids(self, order_ids: List[UUID]) -> List[OrderDetail]:
        """Get multiple orders by IDs"""
        str_ids = [str(oid) for oid in order_ids]

        result = self.client.table("order_details").select(
            "*, orders(*)"
        ).in_("id", str_ids).execute()

        return [self._map_to_order_detail(data) for data in result.data]

    def _map_to_order_detail(self, data: dict) -> OrderDetail:
        """Map database data to OrderDetail entity"""
        order_data = data.get("orders", {})

        return OrderDetail(
            id=UUID(data["id"]),
            order_id=UUID(data["order_id"]),
            start_point=data["start_point"],
            price=float(data["price"]),
            status=data["status"],
            address_detail=data.get("address_detail"),
            area_code=data.get("area_code"),
            location=data.get("location"),
            priority_score=data.get("priority_score"),
            pickup_area_code=data.get("pickup_area_code"),
            pickup_location=data.get("pickup_location"),
            pickup_point=order_data.get("pickup_point"),
            order_type=order_data.get("order_type", "normal"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )