from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.user import User

class UserRepository(ABC):
    """Abstract repository interface cho User"""
    
    @abstractmethod
    async def update_fcm_token(self, user_id: str, fcm_token: str) -> User:
        """Lưu FCM token của user"""
        pass
    
    @abstractmethod
    async def clear_fcm_token(self, user_id: str) -> User:
        """Xóa FCM token khi user logout"""
        pass
    
    @abstractmethod
    async def find_by_fcm_token(self, fcm_token: str) -> Optional[User]:
        """Tìm user theo FCM token"""
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Tìm user theo ID"""
        pass