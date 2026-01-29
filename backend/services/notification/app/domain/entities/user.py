from datetime import datetime
from typing import Optional

class User:
    """
    User entity - đại diện cho user trong hệ thống
    """
    def __init__(
        self,
        id: str,
        email: str,
        full_name: str,
        phone: Optional[str] = None,
        fcm_token: Optional[str] = None,  # FCM token
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.phone = phone
        self.fcm_token = fcm_token  # Firebase Cloud Messaging token
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
    
    def set_fcm_token(self, token: str) -> None:
        """Cập nhật FCM token"""
        self.fcm_token = token
    
    def clear_fcm_token(self) -> None:
        """Xóa FCM token"""
        self.fcm_token = None
    
    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, fcm_token={self.fcm_token})"