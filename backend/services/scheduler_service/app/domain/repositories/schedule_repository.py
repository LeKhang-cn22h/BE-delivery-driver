"""
Schedule Repository Interface (Port)
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from domain.entities.schedule import Schedule, ScheduleItem
from domain.entities.driver import Driver
from domain.entities.order import OrderDetail


class IScheduleRepository(ABC):
    """Schedule repository interface"""

    @abstractmethod
    async def create_schedule(self, schedule: Schedule) -> Schedule:
        """Create new schedule"""
        pass

    @abstractmethod
    async def update_schedule(self, schedule: Schedule) -> Schedule:
        """Update existing schedule"""
        pass

    @abstractmethod
    async def get_schedule_by_id(self, schedule_id: UUID) -> Optional[Schedule]:
        """Get schedule by ID"""
        pass

    @abstractmethod
    async def get_schedules_by_driver(
            self,
            driver_id: UUID,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Schedule]:
        """Get schedules for a driver"""
        pass

    @abstractmethod
    async def get_schedules_by_date(
            self,
            scheduled_date: datetime,
            post_office_id: Optional[UUID] = None
    ) -> List[Schedule]:
        """Get all schedules for a specific date"""
        pass

    @abstractmethod
    async def delete_schedule(self, schedule_id: UUID) -> bool:
        """Delete schedule"""
        pass

    @abstractmethod
    async def add_schedule_items(
            self,
            schedule_id: UUID,
            items: List[ScheduleItem]
    ) -> List[ScheduleItem]:
        """Add items to schedule"""
        pass


class IDriverRepository(ABC):
    """Driver repository interface"""

    @abstractmethod
    async def get_driver_by_id(self, driver_id: UUID) -> Optional[Driver]:
        """Get driver by ID"""
        pass

    @abstractmethod
    async def get_available_drivers(
            self,
            post_office_id: Optional[UUID] = None,
            area_code: Optional[str] = None
    ) -> List[Driver]:
        """Get available drivers for scheduling"""
        pass

    @abstractmethod
    async def get_driver_workload(
            self,
            driver_id: UUID,
            date: datetime
    ) -> int:
        """Get number of orders assigned to driver on a date"""
        pass


class IOrderRepository(ABC):
    """Order repository interface"""

    @abstractmethod
    async def get_pending_orders(
            self,
            post_office_id: Optional[UUID] = None,
            area_code: Optional[str] = None,
            limit: Optional[int] = None
    ) -> List[OrderDetail]:
        """Get pending orders that need scheduling"""
        pass

    @abstractmethod
    async def get_order_by_id(self, order_id: UUID) -> Optional[OrderDetail]:
        """Get order detail by ID"""
        pass

    @abstractmethod
    async def update_order_status(
            self,
            order_detail_id: UUID,
            status: str
    ) -> bool:
        """Update order status"""
        pass

    @abstractmethod
    async def get_orders_by_ids(
            self,
            order_ids: List[UUID]
    ) -> List[OrderDetail]:
        """Get multiple orders by IDs"""
        pass