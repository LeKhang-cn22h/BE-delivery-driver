from domain.repositories.user_repository import UserRepository
from domain.entities.user import User

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def save_fcm_token(self, user_id: str, fcm_token: str) -> User:
        """Lưu FCM token"""
        return await self.user_repository.update_fcm_token(user_id, fcm_token)
    
    async def remove_fcm_token(self, user_id: str) -> User:
        """Xóa FCM token"""
        return await self.user_repository.clear_fcm_token(user_id)