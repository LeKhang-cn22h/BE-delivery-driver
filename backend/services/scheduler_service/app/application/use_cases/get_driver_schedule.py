"""
Use Case: Get Driver Schedule
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from application.dto.schedule_dto import ScheduleDTO, ScheduleItemDTO
from domain.repositories.schedule_repository import IScheduleRepository


class GetDriverScheduleUseCase:
    """Use case for retrieving driver schedules"""

    def __init__(self, schedule_repository: IScheduleRepository):
        self.schedule_repo = schedule_repository

    async def execute(
        self,
        driver_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ScheduleDTO]:
        """
        Get schedules for a specific driver

        Args:
            driver_id: Driver UUID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of schedules for the driver
        """
        schedules = await self.schedule_repo.get_schedules_by_driver(
            driver_id=driver_id,
            start_date=start_date,
            end_date=end_date
        )

        # Convert to DTOs
        schedule_dtos = [
            self._schedule_to_dto(schedule) for schedule in schedules
        ]

        return schedule_dtos

    def _schedule_to_dto(self, schedule) -> ScheduleDTO:
        """Convert Schedule entity to DTO"""
        items_dto = [
            ScheduleItemDTO(
                id=item.id,
                schedule_id=item.schedule_id,
                order_detail_id=item.order_detail_id,
                status=item.status,
                delivered_at=item.delivered_at,
                failure_reason=item.failure_reason,
                queue=item.queue
            )
            for item in schedule.items
        ]

        return ScheduleDTO(
            id=schedule.id,
            driver_id=schedule.driver_id,
            area_code=schedule.area_code,
            scheduled_date=schedule.scheduled_date,
            status=schedule.status,
            total_orders=schedule.total_orders,
            completed_orders=schedule.completed_orders,
            failed_orders=schedule.failed_orders,
            created_at=schedule.created_at,
            updated_at=schedule.updated_at,
            post_office_id=schedule.post_office_id,
            items=items_dto
        )