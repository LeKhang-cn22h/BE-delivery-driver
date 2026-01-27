"""
Use Case: Create Optimized Schedules using Genetic Algorithm
"""
import time
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from application.dto.schedule_dto import (
    CreateScheduleRequest,
    BatchScheduleResponse,
    ScheduleDTO,
    ScheduleItemDTO
)
from domain.repositories.schedule_repository import (
    IScheduleRepository,
    IDriverRepository,
    IOrderRepository
)
from domain.services.schedule_service import ScheduleService


class CreateScheduleUseCase:
    """Use case for creating optimized schedules"""

    def __init__(
        self,
        schedule_repository: IScheduleRepository,
        driver_repository: IDriverRepository,
        order_repository: IOrderRepository
    ):
        self.schedule_repo = schedule_repository
        self.driver_repo = driver_repository
        self.order_repo = order_repository
        self.schedule_service = ScheduleService()

    async def execute(
        self,
        request: CreateScheduleRequest
    ) -> BatchScheduleResponse:
        """
        Execute schedule creation with optimization

        Process:
        1. Get available drivers
        2. Get pending orders
        3. Run GA optimization
        4. Create schedules in database
        5. Return results with metrics
        """
        start_time = time.time()

        # 1. Get available drivers
        if request.driver_ids:
            drivers = []
            for driver_id in request.driver_ids:
                driver = await self.driver_repo.get_driver_by_id(driver_id)
                if driver and driver.is_available():
                    drivers.append(driver)
        else:
            drivers = await self.driver_repo.get_available_drivers(
                post_office_id=request.post_office_id
            )

        if not drivers:
            raise ValueError("No available drivers found")

        # 2. Get pending orders
        orders = await self.order_repo.get_pending_orders(
            post_office_id=request.post_office_id,
            area_code=request.area_code,
            limit=request.order_limit
        )

        if not orders:
            raise ValueError("No pending orders found")

        # 3. Create optimized schedules
        if request.use_genetic_algorithm:
            schedules = self.schedule_service.create_optimized_schedules(
                drivers=drivers,
                orders=orders,
                scheduled_date=request.scheduled_date,
                post_office_id=request.post_office_id
            )
        else:
            # Simple round-robin assignment (fallback)
            schedules = self._create_simple_schedules(
                drivers=drivers,
                orders=orders,
                scheduled_date=request.scheduled_date,
                post_office_id=request.post_office_id
            )

        # 4. Save schedules to database
        created_schedules = []
        for schedule in schedules:
            created_schedule = await self.schedule_repo.create_schedule(schedule)
            created_schedules.append(created_schedule)

            # Update order statuses to 'scheduled'
            for item in schedule.items:
                await self.order_repo.update_order_status(
                    item.order_detail_id,
                    "scheduled"
                )

        # 5. Calculate metrics
        optimization_time = time.time() - start_time
        summary = self.schedule_service.get_schedule_summary(created_schedules)
        summary["optimization_time_seconds"] = round(optimization_time, 2)

        # Convert to DTOs
        schedule_dtos = [
            self._schedule_to_dto(schedule) for schedule in created_schedules
        ]

        return BatchScheduleResponse(
            schedules=schedule_dtos,
            summary=summary,
            optimization_time=optimization_time
        )

    def _create_simple_schedules(
        self,
        drivers,
        orders,
        scheduled_date,
        post_office_id
    ):
        """Simple round-robin assignment (fallback without GA)"""
        from uuid import uuid4
        from app.domain.entities.schedule import Schedule, ScheduleItem

        schedules = []
        driver_assignments = {driver.id: [] for driver in drivers}

        # Round-robin assignment
        for idx, order in enumerate(orders):
            driver_idx = idx % len(drivers)
            driver = drivers[driver_idx]
            driver_assignments[driver.id].append(order)

        # Create schedules
        for driver in drivers:
            assigned_orders = driver_assignments[driver.id]

            if not assigned_orders:
                continue

            schedule = Schedule(
                id=uuid4(),
                driver_id=driver.id,
                area_code=assigned_orders[0].area_code if assigned_orders else None,
                scheduled_date=scheduled_date,
                status="pending",
                total_orders=len(assigned_orders),
                completed_orders=0,
                failed_orders=0,
                created_at=datetime.now(),
                post_office_id=post_office_id
            )

            for queue_pos, order in enumerate(assigned_orders):
                item = ScheduleItem(
                    id=uuid4(),
                    schedule_id=schedule.id,
                    order_detail_id=order.id,
                    status="pending",
                    queue=queue_pos + 1
                )
                schedule.add_item(item)

            schedules.append(schedule)

        return schedules

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