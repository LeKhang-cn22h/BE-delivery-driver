# application/services/driver_workflow_service.py
from domain.repositories.driver_workflow_repository import IDriverWorkflowRepository
from uuid import UUID
from typing import Optional


class DriverWorkflowService:

    def __init__(self, repo: IDriverWorkflowRepository):
        self.repo = repo

    async def start_schedule(self, driver_id: UUID, schedule_id: UUID) -> dict:
        """Driver starts their assigned schedule"""
        return self.repo.start_schedule(driver_id, schedule_id)

    async def take_order(self, driver_id: UUID, order_detail_id: UUID) -> dict:
        """Driver takes an order from schedule"""
        return self.repo.take_order(driver_id, order_detail_id)

    async def mark_picked_up(self, driver_id: UUID, order_detail_id: UUID) -> dict:
        """Driver marks order as picked up"""
        return self.repo.mark_picked_up(driver_id, order_detail_id)

    async def mark_delivered(self, driver_id: UUID, order_detail_id: UUID) -> dict:
        """Driver marks order as delivered"""
        return self.repo.mark_delivered(driver_id, order_detail_id)

    # application/services/driver_workflow_service.py

    async def end_schedule(self, driver_id: UUID, schedule_id: UUID) -> dict:
        """Driver ends their schedule"""
        return self.repo.end_schedule(driver_id, schedule_id)

    async def set_driver_status(self, driver_id: UUID, status: str) -> dict:
        """Update driver status (available, busy, off_duty, inactive)"""
        return self.repo.set_driver_status(driver_id, status)
    async def update_location(
            self,
            driver_id: UUID,
            lat: float,
            lng: float,
            speed: float,
            heading: float
    ) -> dict:
        """Update driver's location"""
        return self.repo.update_location(driver_id, lat, lng, speed, heading)

    async def get_driver_schedule(self, driver_id: UUID, schedule_id: UUID) -> Optional[dict]:
        """Get driver's schedule details"""
        return self.repo.get_driver_schedule(driver_id, schedule_id)