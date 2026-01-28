from typing import List
from uuid import UUID
from domain.entities.driver.driver import Driver
from domain.repositories.driver_repository import DriverRepository

class DriverService:
    def __init__(self, repository: DriverRepository):
        self.repository = repository
        
    def get_driver_by_id(self, driver_id: UUID) -> Driver:
        driver = self.repository.get_by_id(driver_id)
        if not driver:
            raise ValueError(f"Driver with ID {driver_id} not found")
        return driver
    
    def get_drivers_by_post_office_id(self,post_office_id:UUID)->List[Driver]:
        if not post_office_id:
            raise ValueError("Post office ID must be provided")
        return self.repository.get_by_post_office_id(post_office_id)
    
    def get_drivers_by_status(self,status:str)->List[Driver]:
        if not status:
            raise ValueError("Status must be provided")
        return self.repository.get_by_status(status)
    
    def create_driver(self, driver_data) -> Driver:
        # Convert DTO to Entity
        driver = Driver(
            id=None,
            user_id=driver_data.user_id,
            name=driver_data.name,
            phone=driver_data.phone,
            status=driver_data.status,
            post_office_id=driver_data.post_office_id
        )
        return self.repository.create(driver)
    
    def update_driver(self, driver_id: UUID, driver_data) -> Driver:
        driver = self.get_driver_by_id(driver_id)
        driver.name = driver_data.name
        driver.phone = driver_data.phone
        driver.post_office_id = driver_data.post_office_id
        return self.repository.update(driver)
    
    def available_driver(self, driver_id: UUID) -> None:
        driver = self.get_driver_by_id(driver_id) 
        driver.status = "available"               
        self.repository.update_status(driver)     

    def busy_driver(self, driver_id: UUID) -> None:
        driver = self.get_driver_by_id(driver_id)
        driver.status = "busy"
        self.repository.update_status(driver)

    def inactive_driver(self, driver_id: UUID) -> None:
        driver = self.get_driver_by_id(driver_id)
        driver.status = "inactive"
        self.repository.update_status(driver)

    def off_duty_driver(self, driver_id: UUID) -> None:
        driver = self.get_driver_by_id(driver_id)
        driver.status = "off_duty"
        self.repository.update_status(driver)
        