"""
Use Case: Update Schedule
"""
from uuid import UUID

from application.dto.schedule_dto import (
    UpdateScheduleRequest,
    ScheduleResponse,
    ScheduleDTO,
    ScheduleItemDTO
)
from domain.repositories.schedule_repository import (
    IScheduleRepository,
    IOrderRepository
)
from domain.services.schedule_service import ScheduleService
from domain.entities.Schedule import ScheduleItem
from uuid import uuid4


class UpdateScheduleUseCase:
    """Use case for updating schedules"""

    def __init__(
        self,
        schedule_repository: IScheduleRepository,
        order_repository: IOrderRepository
    ):
        self.schedule_repo = schedule_repository
        self.order_repo = order_repository
        self.schedule_service = ScheduleService()

    async def execute(
        self,
        schedule_id: UUID,
        request: UpdateScheduleRequest
    ) -> ScheduleResponse:
        """
        Update existing schedule

        Operations:
        - Update status
        - Add new orders
        - Remove orders
        """
        # Get existing schedule
        schedule = await self.schedule_repo.get_schedule_by_id(schedule_id)

        if not schedule:
            raise ValueError(f"Schedule {schedule_id} not found")

        # Update status if provided
        if request.status:
            schedule.status = request.status

        # Add new orders
        if request.add_order_ids:
            new_orders = await self.order_repo.get_orders_by_ids(
                request.add_order_ids
            )

            for order in new_orders:
                queue_position = schedule.total_orders + 1
                item = ScheduleItem(
                    id=uuid4(),
                    schedule_id=schedule.id,
                    order_detail_id=order.id,
                    status="pending",
                    queue=queue_position
                )
                schedule.add_item(item)

                # Update order status
                await self.order_repo.update_order_status(
                    order.id,
                    "scheduled"
                )

            # Save new items
            await self.schedule_repo.add_schedule_items(
                schedule.id,
                [item for item in schedule.items if item.id in [
                    uuid4() for _ in new_orders
                ]]
            )

        # Remove orders
        if request.remove_order_ids:
            schedule.items = [
                item for item in schedule.items
                if item.order_detail_id not in request.remove_order_ids
            ]
            schedule.total_orders = len(schedule.items)

            # Update removed orders back to pending
            for order_id in request.remove_order_ids:
                await self.order_repo.update_order_status(
                    order_id,
                    "pending"
                )

        # Save updated schedule
        updated_schedule = await self.schedule_repo.update_schedule(schedule)

        # Get metrics
        orders = await self.order_repo.get_orders_by_ids(
            [item.order_detail_id for item in updated_schedule.items]
        )
        metrics = self.schedule_service.calculate_schedule_metrics(
            updated_schedule,
            orders
        )

        # Convert to DTO
        schedule_dto = self._schedule_to_dto(updated_schedule)

        return ScheduleResponse(
            schedule=schedule_dto,
            metrics=metrics
        )

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