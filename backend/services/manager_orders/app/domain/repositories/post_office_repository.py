from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from domain.entities.post_offices.post_office import PostOffice

class PostOfficeRepository(ABC):
    
    @abstractmethod
    def get_all(self) -> List[PostOffice]:
        """Lấy tất cả bưu cục"""
        pass
    
    @abstractmethod
    def get_all_active(self) -> List[PostOffice]:
        """Lấy tất cả bưu cục đang hoạt động"""
        pass
    
    @abstractmethod
    def get_by_id(self, post_office_id: UUID) -> Optional[PostOffice]:
        pass

    @abstractmethod
    def get_by_area_code(self, area_code: str) -> List[PostOffice]:
        pass

    @abstractmethod
    def create(self, post_office: PostOffice) -> PostOffice:
        pass

    @abstractmethod
    def update(self, post_office_id: UUID, status: str) -> None:
        pass