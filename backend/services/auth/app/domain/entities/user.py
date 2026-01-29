# Entity: Đối tượng nghiệp vụ cốt lõi
# - Không phụ thuộc vào framework
# - Chứa business rules cơ bản
# ============================================

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class GeoPoint:
    """Entity cho tọa độ địa lý"""
    lat: float
    lng: float
    
    def to_point_string(self) -> str:
        """Convert sang PostgreSQL POINT format"""
        return f"({self.lng},{self.lat})"
    
    @classmethod
    def from_point_string(cls, point_str: str) -> "GeoPoint":
        """Parse từ PostgreSQL POINT string"""
        point_str = point_str.strip("()")
        lng, lat = map(float, point_str.split(","))
        return cls(lat=lat, lng=lng)


@dataclass
class User:
    """
    User Entity - Đại diện cho user trong hệ thống
    
    Đây là domain model, không phụ thuộc vào:
    - Database schema
    - API response format
    - External services
    """
    id: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    address_detail: Optional[str] = None
    area_code: Optional[str] = None
    location: Optional[GeoPoint] = None
    role: str = "customer"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    fcm_token: Optional[str] = None
    
    def get_display_name(self) -> str:
        """Business logic: Lấy tên hiển thị"""
        return self.full_name or self.email.split('@')[0]
    
    def is_profile_complete(self) -> bool:
        """Business logic: Kiểm tra profile đã đủ thông tin chưa"""
        return all([self.full_name, self.phone, self.address_detail])
    
    def has_location(self) -> bool:
        """Business logic: Kiểm tra có tọa độ vị trí chưa"""
        return self.location is not None


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

@dataclass
class SearchUser:
    id: str
    address_detail: str | None
    area_code: str | None
    location: dict | None