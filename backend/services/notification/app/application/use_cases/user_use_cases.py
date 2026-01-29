from domain.repositories.user_repository import UserRepository
from domain.entities.user import User

class SaveFCMTokenUseCase:
    """Use case: Lưu FCM token"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: str, fcm_token: str) -> User:
        return await self.user_repository.update_fcm_token(user_id, fcm_token)

class RemoveFCMTokenUseCase:
    """Use case: Xóa FCM token"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def execute(self, user_id: str) -> User:
        return await self.user_repository.clear_fcm_token(user_id)