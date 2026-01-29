from typing import Optional
import logging
from domain.entities.user import User
from domain.repositories.user_repository import UserRepository
from infrastructure.database.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class SupabaseUserRepository(UserRepository):
    """Implement UserRepository với Supabase"""
    
    def __init__(self):
        self.client = SupabaseClient.get_client()
    
    def _map_to_entity(self, user_data: dict) -> User:
        """Map Supabase data -> User entity"""
        # Chỉ lấy fields cần thiết từ User entity
        return User(
            id=user_data.get('id'),
            email=user_data.get('email'),
            full_name=user_data.get('full_name'),  # ← Field đúng từ entity
            phone=user_data.get('phone'),
            fcm_token=user_data.get('fcm_token'),
            is_active=user_data.get('is_active', True),
            created_at=user_data.get('created_at'),
            updated_at=user_data.get('updated_at'),
        )
    
    async def update_fcm_token(self, user_id: str, fcm_token: str) -> User:
        """Lưu FCM token vào Supabase"""
        try:
            logger.info(f"Updating FCM token for user {user_id}")
            
            response = self.client.table('users').update({
                'fcm_token': fcm_token
            }).eq('id', user_id).execute()
            
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                logger.info(f"FCM token updated successfully for user {user_id}")
                return self._map_to_entity(user_data)
            
            logger.error(f"User {user_id} not found")
            raise ValueError(f"User {user_id} not found")
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error updating FCM token: {str(e)}")
            raise ValueError(f"Failed to update FCM token: {str(e)}")
    
    
    async def clear_fcm_token(self, user_id: str) -> User:
        """Xóa FCM token"""
        try:
            logger.info(f"Clearing FCM token for user {user_id}")
            
            response = self.client.table('users').update({
                'fcm_token': None
            }).eq('id', user_id).execute()
            
            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                logger.info(f"FCM token cleared successfully for user {user_id}")
                return self._map_to_entity(user_data)
            
            logger.error(f"User {user_id} not found")
            raise ValueError(f"User {user_id} not found")
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error clearing FCM token: {str(e)}")
            raise ValueError(f"Failed to clear FCM token: {str(e)}")
    
    
    async def find_by_fcm_token(self, fcm_token: str) -> Optional[User]:
        """Tìm user theo FCM token"""
        try:
            logger.info(f"Finding user by FCM token")
            
            response = self.client.table('users').select('*').eq(
                'fcm_token', fcm_token
            ).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"User found by FCM token")
                return self._map_to_entity(response.data[0])
            
            logger.warning(f"User not found by FCM token")
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by FCM token: {str(e)}")
            raise ValueError(f"Failed to find user: {str(e)}")
    
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Tìm user theo ID"""
        try:
            logger.info(f"Finding user by ID: {user_id}")
            
            response = self.client.table('users').select('*').eq(
                'id', user_id
            ).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"User found by ID")
                return self._map_to_entity(response.data[0])
            
            logger.warning(f"User not found by ID: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding user by ID: {str(e)}")
            raise ValueError(f"Failed to find user: {str(e)}")
