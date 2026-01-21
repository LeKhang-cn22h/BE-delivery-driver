
# Entity: Đối tượng nghiệp vụ cốt lõi
# - Không phụ thuộc vào framework
# - Chứa business rules cơ bản
# ============================================

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """
    User Entity - Đại diện cho user trong hệ thống
    
    Đây là domain entity, không phụ thuộc vào:
    - Database schema
    - API response format
    - External services
    """
    id: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def get_display_name(self) -> str:
        """Business logic: Lấy tên hiển thị"""
        return self.full_name or self.email.split('@')[0]
    
    def is_profile_complete(self) -> bool:
        """Business logic: Kiểm tra profile đã đủ thông tin chưa"""
        return all([self.full_name, self.phone])


@dataclass
class AuthTokens:
    """
    Auth Tokens Entity
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


@dataclass
class AuthResult:
    """
    Kết quả authentication
    """
    tokens: AuthTokens
    user: User