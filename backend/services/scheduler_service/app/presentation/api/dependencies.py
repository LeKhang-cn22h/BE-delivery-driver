"""
Dependency Injection Container
"""
from functools import lru_cache

from app.infrastructure.database.repositories.schedule_repository_impl import (
    ScheduleRepositoryImpl,
    DriverRepositoryImpl,
    OrderRepositoryImpl
)
from app.application.use_cases.create_schedule import CreateScheduleUseCase
from app.application.use_cases.get_driver_schedule import GetDriverScheduleUseCase
from app.application.use_cases.update_schedule import UpdateScheduleUseCase
from app.domain.repositories.schedule_repository import (
    IScheduleRepository,
    IDriverRepository,
    IOrderRepository
)


# Repository Instances
@lru_cache()
def get_schedule_repository() -> IScheduleRepository:
    """Get schedule repository instance"""
    return ScheduleRepositoryImpl()


@lru_cache()
def get_driver_repository() -> IDriverRepository:
    """Get driver repository instance"""
    return DriverRepositoryImpl()


@lru_cache()
def get_order_repository() -> IOrderRepository:
    """Get order repository instance"""
    return OrderRepositoryImpl()


# Use Case Instances
def get_create_schedule_use_case() -> CreateScheduleUseCase:
    """Get create schedule use case"""
    return CreateScheduleUseCase(
        schedule_repository=get_schedule_repository(),
        driver_repository=get_driver_repository(),
        order_repository=get_order_repository()
    )


def get_driver_schedule_use_case() -> GetDriverScheduleUseCase:
    """Get driver schedule use case"""
    return GetDriverScheduleUseCase(
        schedule_repository=get_schedule_repository()
    )


def get_update_schedule_use_case() -> UpdateScheduleUseCase:
    """Get update schedule use case"""
    return UpdateScheduleUseCase(
        schedule_repository=get_schedule_repository(),
        order_repository=get_order_repository()
    )