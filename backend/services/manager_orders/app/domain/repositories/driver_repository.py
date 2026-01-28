from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from domain.entities.driver.driver import Driver

class DriverRepository(ABC):
    @abstractmethod
    def get_by_id(self, driver_id:UUID) -> Optional[Driver]:
        pass

    @abstractmethod
    def get_by_post_office_id(self, post_office_id:UUID) ->List[Driver]:
        pass

    @abstractmethod
    def get_by_status(self,status:str) ->List[Driver]:
        pass
    
    @abstractmethod
    def create(self,driver:Driver) ->Driver:
        pass

    @abstractmethod
    def update(self,driver_id:UUID) ->None:
        pass

    @abstractmethod
    def update_status(self,driver:Driver,status:str) ->Driver:
        pass
