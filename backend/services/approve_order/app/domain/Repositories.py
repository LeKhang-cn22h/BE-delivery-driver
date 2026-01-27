from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from domain.models import OrderDetail, Schedule, ScheduleItem


class IOrderRepository(ABC):
    """Interface cho Order Repository"""

    @abstractmethod
    async def get_pending_order_details(self, post_office_id: str) -> List[OrderDetail]:
        """
        Lấy tất cả order details có status = 'pending'
        thuộc về post_office_id
        """
        pass

    @abstractmethod
    async def get_order_details_by_area(
            self,
            post_office_id: str,
            area_code: str
    ) -> List[OrderDetail]:
        """
        Lấy order details theo area_code và post_office_id
        """
        pass

    @abstractmethod
    async def update_order_detail_status(
            self,
            order_detail_id: str,
            status: str
    ) -> bool:
        """Cập nhật status của order detail"""
        pass


class IScheduleRepository(ABC):
    """Interface cho Schedule Repository"""

    @abstractmethod
    async def create_schedule(self, schedule_data: dict) -> Schedule:
        """Tạo schedule mới"""
        pass

    @abstractmethod
    async def get_schedule_by_id(self, schedule_id: str) -> Optional[Schedule]:
        """Lấy schedule theo ID"""
        pass

    @abstractmethod
    async def update_schedule(
            self,
            schedule_id: str,
            update_data: dict
    ) -> Schedule:
        """Cập nhật thông tin schedule"""
        pass

    @abstractmethod
    async def get_schedules_by_date_and_area(
            self,
            post_office_id: str,
            scheduled_date: datetime,
            area_code: str
    ) -> Optional[Schedule]:
        """Kiểm tra xem đã có schedule cho ngày và vùng này chưa"""
        pass


class IScheduleItemRepository(ABC):
    """Interface cho Schedule Item Repository"""

    @abstractmethod
    async def create_schedule_item(self, item_data: dict) -> ScheduleItem:
        """Tạo schedule item mới"""
        pass

    @abstractmethod
    async def create_schedule_items_batch(
            self,
            items_data: List[dict]
    ) -> List[ScheduleItem]:
        """Tạo nhiều schedule items cùng lúc"""
        pass

    @abstractmethod
    async def get_items_by_schedule(
            self,
            schedule_id: str
    ) -> List[ScheduleItem]:
        """Lấy tất cả items của một schedule"""
        pass

    @abstractmethod
    async def get_max_queue_number(self, schedule_id: str) -> int:
        """Lấy số queue lớn nhất trong schedule"""
        pass