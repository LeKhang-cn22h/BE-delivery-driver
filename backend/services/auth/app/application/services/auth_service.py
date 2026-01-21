# ============================================
# application/services/auth_service.py
# ============================================
#
# Application Service (Use Cases)
# - Orchestrate business logic
# - Gọi repository để thao tác data
# - Convert Entity ↔ Schema
# ============================================

from typing import Optional
from fastapi import HTTPException
import logging

from domain.repositories.auth_repository import AuthRepositoryInterface
from application.schemas.auth_schemas import (
    RegisterRequest,
    LoginRequest,
    UpdateProfileRequest,
    AuthResponse,
    UserResponse,
    MessageResponse
)

logger = logging.getLogger(__name__)


class AuthService:
    """
    Auth Service - Application layer
    
    Chứa use cases cho authentication:
    - Register
    - Login
    - Logout
    - Refresh token
    - Get/Update profile
    - Reset password
    """
    
    def __init__(self, auth_repository: AuthRepositoryInterface):
        """
        Dependency Injection
        
        Nhận repository interface, không quan tâm implementation cụ thể
        → Dễ test, dễ swap implementation
        """
        self.auth_repository = auth_repository
    
    # ========================================
    # REGISTER
    # ========================================
    async def register(self, data: RegisterRequest) -> AuthResponse:
        """
        Use case: Đăng ký tài khoản
        
        Flow:
        1. Validate data (Pydantic đã làm)
        2. Gọi repository để tạo user
        3. Convert result thành response
        """
        try:
            result = await self.auth_repository.register(
                email=data.email,
                password=data.password,
                full_name=data.full_name,
                phone=data.phone
            )
            
            return self._to_auth_response(result)
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # ========================================
    # LOGIN
    # ========================================
    async def login(self, data: LoginRequest) -> AuthResponse:
        """Use case: Đăng nhập"""
        try:
            result = await self.auth_repository.login(
                email=data.email,
                password=data.password
            )
            
            return self._to_auth_response(result)
            
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    # ========================================
    # LOGOUT
    # ========================================
    async def logout(self, access_token: str) -> MessageResponse:
        """Use case: Đăng xuất"""
        await self.auth_repository.logout(access_token)
        return MessageResponse(message="Đăng xuất thành công")
    
    # ========================================
    # REFRESH TOKEN
    # ========================================
    async def refresh_token(self, refresh_token: str) -> AuthResponse:
        """Use case: Làm mới token"""
        try:
            result = await self.auth_repository.refresh_token(refresh_token)
            return self._to_auth_response(result)
            
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    # ========================================
    # GET CURRENT USER
    # ========================================
    async def get_current_user(self, access_token: str) -> UserResponse:
        """Use case: Lấy thông tin user hiện tại"""
        try:
            user = await self.auth_repository.get_user_by_token(access_token)
            return self._to_user_response(user)
            
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
    
    # ========================================
    # UPDATE PROFILE
    # ========================================
    async def update_profile(
        self,
        access_token: str,
        data: UpdateProfileRequest
    ) -> UserResponse:
        """Use case: Cập nhật profile"""
        try:
            user = await self.auth_repository.update_user(
                access_token=access_token,
                full_name=data.full_name,
                phone=data.phone,
                avatar_url=data.avatar_url
            )
            return self._to_user_response(user)
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # ========================================
    # RESET PASSWORD
    # ========================================
    async def reset_password_request(self, email: str) -> MessageResponse:
        """Use case: Gửi email reset password"""
        await self.auth_repository.reset_password_request(email)
        return MessageResponse(
            message="Nếu email tồn tại, bạn sẽ nhận được hướng dẫn đặt lại mật khẩu"
        )
    
    # ========================================
    # HELPER: Convert Entity → Response
    # ========================================
    def _to_auth_response(self, result) -> AuthResponse:
        """Convert AuthResult entity thành AuthResponse schema"""
        return AuthResponse(
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            token_type=result.tokens.token_type,
            expires_in=result.tokens.expires_in,
            user=self._to_user_response(result.user)
        )
    
    def _to_user_response(self, user) -> UserResponse:
        """Convert User entity thành UserResponse schema"""
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            created_at=user.created_at
        )