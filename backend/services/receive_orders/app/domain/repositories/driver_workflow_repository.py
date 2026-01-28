# domain/repositories/driver_workflow_repository.py
from abc import ABC, abstractmethod
from uuid import UUID
from typing import Optional


class IDriverWorkflowRepository(ABC):

    @abstractmethod
    def start_schedule(self, driver_id: UUID, schedule_id: UUID) -> dict:
        """Driver starts their assigned schedule"""
        pass

    @abstractmethod
    def take_order(self, driver_id: UUID, order_detail_id: UUID) -> dict:
        """Driver takes an order from their schedule"""
        pass

    @abstractmethod
    def mark_picked_up(self, driver_id: UUID, order_detail_id: UUID) -> dict:
        """Driver marks order as picked up"""
        pass

    @abstractmethod
    def mark_delivered(self, driver_id: UUID, order_detail_id: UUID) -> dict:
        """Driver marks order as delivered"""
        pass

    @abstractmethod
    def update_location(
            self,
            driver_id: UUID,
            lat: float,
            lng: float,
            speed: float,
            heading: float
    ) -> dict:
        """Update driver's current location"""
        pass

    @abstractmethod
    def get_driver_schedule(self, driver_id: UUID, schedule_id: UUID) -> Optional[dict]:
        """Get driver's schedule details"""
        pass

    # domain/repositories/driver_workflow_repository.py

    @abstractmethod
    def end_schedule(self, driver_id: UUID, schedule_id: UUID) -> dict:
        """Driver ends their schedule"""
        pass

    @abstractmethod
    def set_driver_status(self, driver_id: UUID, status: str) -> dict:
        """Update driver status"""
        pass