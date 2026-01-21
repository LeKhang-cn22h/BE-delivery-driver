# ============================================
# application/schemas/auth_schemas.py
# ============================================
#
# Pydantic schemas cho API
# - Request validation
# - Response serialization
# - Auto-generate API docs
# ============================================

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


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


class LoginRequest(BaseModel):
    """Request body cho đăng nhập"""
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., example="123456")


class RefreshTokenRequest(BaseModel):
    """Request body cho refresh token"""
    refresh_token: str = Field(..., description="Refresh token từ login")


class UpdateProfileRequest(BaseModel):
    """Request body cho cập nhật profile"""
    full_name: Optional[str] = Field(None, min_length=2)
    phone: Optional[str] = Field(None, pattern=r"^[0-9]{10,11}$")
    avatar_url: Optional[str] = None


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
    created_at: Optional[datetime] = None
    
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