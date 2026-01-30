# Pydantic schemas cho API
# - Request validation
# - Response serialization
# - Auto-generate API docs
# ============================================

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


# ============================================
# SHARED SCHEMAS
# ============================================

class GeoPointDTO(BaseModel):
    """Tọa độ địa lý"""
    lat: float = Field(..., description="Vĩ độ")
    lng: float = Field(..., description="Kinh độ")

    @classmethod
    def from_point_string(cls, p: str):
        """Convert từ PostgreSQL POINT string: '(lng,lat)'"""
        p = p.strip("()")
        lng, lat = map(float, p.split(","))
        return cls(lat=lat, lng=lng)
    
    def to_point_string(self) -> str:
        """Convert sang PostgreSQL POINT format"""
        return f"({self.lng},{self.lat})"


# ============================================
# REQUEST SCHEMAS
# ============================================

class RegisterRequest(BaseModel):
    """Request body cho đăng ký"""
    email: EmailStr = Field(
        ...,
        description="Email đăng ký",
        example="user@example.com"
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Mật khẩu (tối thiểu 6 ký tự)",
        example="123456"
    )
    full_name: str = Field(
        ...,
        min_length=2,
        description="Họ và tên",
        example="Nguyễn Văn A"
    )
    phone: Optional[str] = Field(
        None,
        pattern=r"^[0-9]{10,11}$",
        description="Số điện thoại (10-11 số)",
        example="0901234567"
    )
    address_detail: Optional[str] = Field(
        None,
        description="Địa chỉ chi tiết",
        example="123 Nguyễn Huệ, Quận 1"
    )
    area_code: Optional[str] = Field(
        None,
        description="Mã khu vực",
        example="Q1"
    )
    location: Optional[GeoPointDTO] = Field(
        None,
        description="Tọa độ vị trí người dùng"
    )

    @field_validator("location", mode="before")
    @classmethod
    def parse_location(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return GeoPointDTO.from_point_string(v)
        return v


class LoginRequest(BaseModel):
    """Request body cho đăng nhập"""
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., example="123456")
    fcm_token: Optional[str] = Field(
        None,
        description="Firebase Cloud Messaging token cho push notification"
    )


class RefreshTokenRequest(BaseModel):
    """Request body cho refresh token"""
    refresh_token: str = Field(..., description="Refresh token từ login")


class UpdateProfileRequest(BaseModel):
    """Request body cho cập nhật profile"""
    full_name: Optional[str] = Field(None, min_length=2, description="Họ và tên")
    phone: Optional[str] = Field(
        None,
        pattern=r"^[0-9]{10,11}$",
        description="Số điện thoại"
    )
    avatar_url: Optional[str] = Field(None, description="URL avatar")
    address_detail: Optional[str] = Field(None, description="Địa chỉ chi tiết")
    area_code: Optional[str] = Field(None, description="Mã khu vực")
    location: Optional[GeoPointDTO] = Field(None, description="Tọa độ vị trí")
    fcm_token: Optional[str] = Field(None, description="FCM token")

    @field_validator("location", mode="before")
    @classmethod
    def parse_location(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return GeoPointDTO.from_point_string(v)
        return v


class ResetPasswordRequest(BaseModel):
    """Request body cho reset password"""
    email: EmailStr


# ============================================
# RESPONSE SCHEMAS
# ============================================

class UserResponse(BaseModel):
    """Response chứa thông tin user"""
    id: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    address_detail: Optional[str] = None
    area_code: Optional[str] = None
    location: Optional[GeoPointDTO] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    fcm_token: Optional[str] = None
    post_office_id:Optional[str]=None
    
    @field_validator("location", mode="before")
    @classmethod
    def parse_location(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return GeoPointDTO.from_point_string(v)
        return v
    
    class Config:
        from_attributes = True  # Cho phép convert từ Entity


class TokensResponse(BaseModel):
    """Response chứa tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(BaseModel):
    """Response cho login/register thành công"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class MessageResponse(BaseModel):
    """Response message đơn giản""" 
    message: str
    success: bool = True