
# API Router - Presentation layer
# - Định nghĩa HTTP endpoints
# - Handle request/response
# - Dependency injection
# ============================================

from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Optional

from application.schemas.auth_schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    UpdateProfileRequest,
    ResetPasswordRequest,
    AuthResponse,
    UserResponse,
    MessageResponse
)
from application.services.auth_service import AuthService
from infrastructure.repositories.supabase_auth_repository import SupabaseAuthRepository

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


# ============================================
# DEPENDENCY INJECTION
# ============================================

def get_auth_service() -> AuthService:
    """
    Dependency: Tạo AuthService với SupabaseRepository
    
    Đây là nơi "wire" các dependencies:
    - AuthService cần AuthRepositoryInterface
    - Inject SupabaseAuthRepository (implementation)
    """
    repository = SupabaseAuthRepository()
    return AuthService(auth_repository=repository)


async def get_token_from_header(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Dependency: Extract token từ Authorization header
    
    Header format: "Bearer <token>"
    """
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required"
        )
    
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Use: Bearer <token>"
        )
    
    return parts[1]


# ============================================
# ENDPOINTS
# ============================================

@router.post(
    "/register",
    response_model=AuthResponse,
    summary="Đăng ký tài khoản mới"
)
async def register(
    data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Đăng ký tài khoản mới
    
    **Request body:**
    ```json
    {
        "email": "user@example.com",
        "password": "123456",
        "full_name": "Nguyễn Văn A",
        "phone": "0901234567"
    }
    ```
    """
    return await auth_service.register(data)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Đăng nhập"
)
async def login(
    data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Đăng nhập với email và password
    
    **Response:** access_token, refresh_token và thông tin user
    """
    return await auth_service.login(data)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Đăng xuất"
)
async def logout(
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Đăng xuất - invalidate session
    
    **Header:** `Authorization: Bearer <access_token>`
    """
    return await auth_service.logout(token)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Làm mới access token"
)
async def refresh_token(
    data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Lấy access token mới từ refresh token
    
    **Request body:**
    ```json
    {
        "refresh_token": "your_refresh_token"
    }
    ```
    """
    return await auth_service.refresh_token(data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Lấy thông tin user hiện tại"
)
async def get_current_user(
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Lấy thông tin user từ access token
    
    **Header:** `Authorization: Bearer <access_token>`
    """
    return await auth_service.get_current_user(token)

@router.get("/search")
async def search_user_by_phone_or_mail(data:str,auth_service: AuthService = Depends(get_auth_service)):
    return await auth_service.search_user_by_phone_or_mail(data)

@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Cập nhật profile"
)
async def update_profile(
    data: UpdateProfileRequest,
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Cập nhật thông tin profile
    
    **Header:** `Authorization: Bearer <access_token>`
    
    **Request body:** (chỉ gửi field muốn update)
    ```json
    {
        "full_name": "Tên mới",
        "phone": "0909999999"
    }
    ```
    """
    return await auth_service.update_profile(token, data)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Yêu cầu đặt lại mật khẩu"
)
async def reset_password(
    data: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Gửi email hướng dẫn đặt lại mật khẩu
    """
    return await auth_service.reset_password_request(data.email)
@router.get("/verify", summary="Verify token (internal)")
async def verify_token(
    token: str = Depends(get_token_from_header),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Internal endpoint - Called by Gateway
    Verify token validity and return user info
    """
    try:
        user = await auth_service.get_current_user(token)
        return {
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": getattr(user, 'role', 'user'),
            "phone": user.phone
        }
    except HTTPException:
        raise

@router.get("/health", summary="Health check")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth_service"}