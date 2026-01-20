
# Proxy router để forward requests từ Gateway
# đến Auth Service
#
# Gateway pattern:
# Client → Gateway (8000) → Auth Service (7000)
# ============================================

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import os
import sys

# Thêm path để import HTTPClient
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.http_client import HTTPClient

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

# ============================================
# HTTP Client cho Auth Service
# ============================================
AUTH_SERVICE_URL = os.getenv(
    "AUTH_SERVICE_URL",
    "http://auth_service:7000"  # Tên container trong docker-compose
)
auth_client = HTTPClient(AUTH_SERVICE_URL)


# ============================================
# POST /register - Đăng ký
# ============================================
@router.post("/register", summary="Đăng ký tài khoản mới")
async def register(request: Request):
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
    body = await request.json()
    return await auth_client.post("/api/v1/auth/register", body)


# ============================================
# POST /login - Đăng nhập
# ============================================
@router.post("/login", summary="Đăng nhập")
async def login(request: Request):
    """
    Đăng nhập với email và password
    
    **Request body:**
    ```json
    {
        "email": "user@example.com",
        "password": "123456"
    }
    ```
    
    **Response:**
    ```json
    {
        "access_token": "eyJ...",
        "refresh_token": "...",
        "token_type": "bearer",
        "expires_in": 3600,
        "user": {...}
    }
    ```
    """
    body = await request.json()
    return await auth_client.post("/api/v1/auth/login", body)


# ============================================
# POST /logout - Đăng xuất
# ============================================
@router.post("/logout", summary="Đăng xuất")
async def logout(authorization: Optional[str] = Header(None)):
    """
    Đăng xuất - invalidate session
    
    **Header required:** `Authorization: Bearer <access_token>`
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Forward header to auth service
    headers = {"Authorization": authorization}
    return await auth_client.request(
        "POST", 
        "/api/v1/auth/logout", 
        headers=headers
    )


# ============================================
# POST /refresh - Refresh token
# ============================================
@router.post("/refresh", summary="Làm mới access token")
async def refresh_token(request: Request):
    """
    Lấy access token mới từ refresh token
    
    **Request body:**
    ```json
    {
        "refresh_token": "your_refresh_token"
    }
    ```
    """
    body = await request.json()
    return await auth_client.post("/api/v1/auth/refresh", body)


# ============================================
# GET /me - Lấy thông tin user
# ============================================
@router.get("/me", summary="Lấy thông tin user hiện tại")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Lấy thông tin user từ access token
    
    **Header required:** `Authorization: Bearer <access_token>`
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    headers = {"Authorization": authorization}
    return await auth_client.request("GET", "/api/v1/auth/me", headers=headers)


# ============================================
# PATCH /me - Cập nhật profile
# ============================================
@router.patch("/me", summary="Cập nhật thông tin profile")
async def update_profile(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Cập nhật thông tin profile
    
    **Header required:** `Authorization: Bearer <access_token>`
    
    **Request body:**
    ```json
    {
        "full_name": "Tên mới",
        "phone": "0909999999"
    }
    ```
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    body = await request.json()
    headers = {"Authorization": authorization}
    
    return await auth_client.request(
        "PATCH",
        "/api/v1/auth/me",
        json_data=body,
        headers=headers
    )


# ============================================
# POST /reset-password - Quên mật khẩu
# ============================================
@router.post("/reset-password", summary="Yêu cầu đặt lại mật khẩu")
async def reset_password(request: Request):
    """
    Gửi email hướng dẫn đặt lại mật khẩu
    
    **Request body:**
    ```json
    {
        "email": "user@example.com"
    }
    ```
    """
    body = await request.json()
    return await auth_client.post("/api/v1/auth/reset-password", body)