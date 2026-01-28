# gateway/app/routers/notification_proxy.py
"""
Notification Service Proxy Router
Forward requests từ Gateway đến Notification Microservice
"""

from fastapi import APIRouter, Request, HTTPException, Query, status
from typing import Optional
import httpx
import os
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

NOTIFICATION_SERVICE_URL = os.getenv(
    "NOTIFICATION_SERVICE_URL",
    "http://notification_service:8003"
)


async def proxy_request(
    method: str,
    path: str,
    request: Request,
    params: dict = None,
    body: bytes = None
) -> dict:
    """
    Forward request đến notification service
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: Endpoint path (e.g., "/users/123/fcm", "/{id}")
        request: FastAPI Request object
        params: Query parameters
        body: Request body bytes
    """
    
    url = f"{NOTIFICATION_SERVICE_URL}/api/v1/notifications{path}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Lấy body nếu là POST/PUT/DELETE
            request_body = body if body is not None else (
                await request.body() if method in ["POST", "PUT", "DELETE"] else None
            )
            
            response = await client.request(
                method=method,
                url=url,
                params=params,
                headers=dict(request.headers),
                content=request_body,
                follow_redirects=True
            )
            
            logger.info(f"✓ Notification {method} {path} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error(f"✗ Notification service error: {response.text}")
                return {
                    "status_code": response.status_code,
                    "content": response.json() if response.text else {}
                }
            
            return {
                "status_code": response.status_code,
                "content": response.json() if response.text else {}
            }
            
    except httpx.TimeoutException:
        logger.error(f"✗ Notification service timeout: {path}")
        raise HTTPException(
            status_code=504,
            detail="Notification service timeout"
        )
    except Exception as e:
        logger.error(f"✗ Notification service error: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Notification service unavailable: {str(e)}"
        )


# ===== FCM TOKEN ENDPOINTS =====

@router.post(
    "/users/{user_id}/fcm",
    status_code=status.HTTP_200_OK,
    summary="Lưu FCM token của user",
    description="Lưu Firebase Cloud Messaging token cho thiết bị của user"
)
async def save_fcm_token(
    user_id: str,
    request: Request
):
    """Lưu FCM token của user"""
    try:
        result = await proxy_request("POST", f"/users/{user_id}/fcm", request)
        
        if result["status_code"] >= 400:
            raise HTTPException(
                status_code=result["status_code"],
                detail=result["content"].get("detail", "Failed to save FCM token")
            )
        
        return result["content"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in save_fcm_token proxy: {str(e)}")
        raise HTTPException(status_code=502, detail="Failed to save FCM token")


@router.delete(
    "/users/{user_id}/fcm",
    status_code=status.HTTP_200_OK,
    summary="Xóa FCM token của user",
    description="Xóa Firebase Cloud Messaging token khi user logout"
)
async def remove_fcm_token(
    user_id: str,
    request: Request
):
    """Xóa FCM token khi user logout"""
    try:
        result = await proxy_request("DELETE", f"/users/{user_id}/fcm", request)
        
        if result["status_code"] >= 400:
            raise HTTPException(
                status_code=result["status_code"],
                detail=result["content"].get("detail", "Failed to remove FCM token")
            )
        
        return result["content"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in remove_fcm_token proxy: {str(e)}")
        raise HTTPException(status_code=502, detail="Failed to remove FCM token")


# ===== NOTIFICATION ENDPOINTS =====

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Tạo thông báo mới",
    description="Tạo một thông báo mới cho user"
)
async def create_notification(request: Request):
    """Tạo thông báo mới"""
    try:
        result = await proxy_request("POST", "/", request)
        
        if result["status_code"] >= 400:
            raise HTTPException(
                status_code=result["status_code"],
                detail=result["content"].get("detail", "Failed to create notification")
            )
        
        return result["content"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_notification proxy: {str(e)}")
        raise HTTPException(status_code=502, detail="Failed to create notification")


@router.get(
    "/",
    summary="Lấy danh sách thông báo",
    description="Lấy danh sách thông báo của user với filter và phân trang"
)
async def get_notifications(
    user_id: str = Query(..., description="ID của user"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái (UNREAD, READ)"),
    type: Optional[str] = Query(None, description="Lọc theo loại"),
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số lượng mỗi trang"),
    request: Request = None
):
    """Lấy danh sách thông báo"""
    try:
        params = {
            "user_id": user_id,
            "page": page,
            "page_size": page_size
        }
        
        if status:
            params["status"] = status
        if type:
            params["type"] = type
        
        result = await proxy_request("GET", "/", request, params=params)
        
        if result["status_code"] >= 400:
            raise HTTPException(
                status_code=result["status_code"],
                detail=result["content"].get("detail", "Failed to get notifications")
            )
        
        return result["content"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_notifications proxy: {str(e)}")
        raise HTTPException(status_code=502, detail="Failed to get notifications")


@router.get(
    "/unread/count",
    summary="Đếm số thông báo chưa đọc",
    description="Lấy số lượng thông báo chưa đọc của user"
)
async def get_unread_count(
    user_id: str = Query(..., description="ID của user"),
    request: Request = None
):
    """Đếm số thông báo chưa đọc"""
    try:
        params = {"user_id": user_id}
        result = await proxy_request("GET", "/unread/count", request, params=params)
        
        if result["status_code"] >= 400:
            raise HTTPException(
                status_code=result["status_code"],
                detail=result["content"].get("detail", "Failed to get unread count")
            )
        
        return result["content"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_unread_count proxy: {str(e)}")
        raise HTTPException(status_code=502, detail="Failed to get unread count")


@router.get(
    "/{notification_id}",
    summary="Lấy thông báo theo ID",
    description="Lấy chi tiết một thông báo"
)
async def get_notification(
    notification_id: str,
    request: Request
):
    """Lấy thông báo theo ID"""
    try:
        result = await proxy_request("GET", f"/{notification_id}", request)
        
        if result["status_code"] >= 400:
            raise HTTPException(
                status_code=result["status_code"],
                detail=result["content"].get("detail", "Notification not found")
            )
        
        return result["content"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_notification proxy: {str(e)}")
        raise HTTPException(status_code=502, detail="Failed to get notification")


@router.put(
    "/{notification_id}/read",
    status_code=status.HTTP_200_OK,
    summary="Đánh dấu đã đọc",
    description="Đánh dấu một thông báo đã được đọc"
)
async def mark_as_read(
    notification_id: str,
    request: Request
):
    """Đánh dấu đã đọc"""
    try:
        result = await proxy_request("PUT", f"/{notification_id}/read", request)
        
        if result["status_code"] >= 400:
            raise HTTPException(
                status_code=result["status_code"],
                detail=result["content"].get("detail", "Failed to mark as read")
            )
        
        return result["content"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mark_as_read proxy: {str(e)}")
        raise HTTPException(status_code=502, detail="Failed to mark as read")


@router.put(
    "/read-all",
    status_code=status.HTTP_200_OK,
    summary="Đánh dấu tất cả đã đọc",
    description="Đánh dấu tất cả thông báo của user đã được đọc"
)
async def mark_all_as_read(
    user_id: str = Query(..., description="ID của user"),
    request: Request = None
):
    """Đánh dấu tất cả đã đọc"""
    try:
        params = {"user_id": user_id}
        result = await proxy_request("PUT", "/read-all", request, params=params)
        
        if result["status_code"] >= 400:
            raise HTTPException(
                status_code=result["status_code"],
                detail=result["content"].get("detail", "Failed to mark all as read")
            )
        
        return result["content"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in mark_all_as_read proxy: {str(e)}")
        raise HTTPException(status_code=502, detail="Failed to mark all as read")


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_200_OK,
    summary="Xóa thông báo",
    description="Xóa một thông báo (soft delete)"
)
async def delete_notification(
    notification_id: str,
    request: Request
):
    """Xóa thông báo"""
    try:
        result = await proxy_request("DELETE", f"/{notification_id}", request)
        
        if result["status_code"] >= 400:
            raise HTTPException(
                status_code=result["status_code"],
                detail=result["content"].get("detail", "Failed to delete notification")
            )
        
        return result["content"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_notification proxy: {str(e)}")
        raise HTTPException(status_code=502, detail="Failed to delete notification")


# ===== MULTI-CHANNEL NOTIFICATION ENDPOINT =====

@router.post(
    "/send-multi-channel",
    status_code=status.HTTP_200_OK,
    summary="Gửi thông báo multi-channel",
    description="Gửi thông báo qua email (customer) hoặc push (shipper)"
)
async def send_multi_channel_notification(
    user_id: str = Query(..., description="ID của user"),
    user_type: str = Query(..., description="Loại user: 'customer' hoặc 'shipper'"),
    title: str = Query(..., description="Tiêu đề thông báo"),
    body: str = Query(..., description="Nội dung thông báo"),
    notification_type: str = Query("promotion", description="Loại thông báo: order, delivery, promotion"),
    user_email: Optional[str] = Query(None, description="Email của customer (nếu là customer)"),
    device_token: Optional[str] = Query(None, description="FCM token của shipper (nếu là shipper)"),
    request: Request = None
):
    """
    Gửi thông báo qua email hoặc push notification
    
    - Nếu user_type = 'customer' → Gửi email
    - Nếu user_type = 'shipper' → Gửi push notification (FCM)
    """
    try:
        params = {
            "user_id": user_id,
            "user_type": user_type,
            "title": title,
            "body": body,
            "notification_type": notification_type
        }
        
        if user_email:
            params["user_email"] = user_email
        if device_token:
            params["device_token"] = device_token
        
        result = await proxy_request("POST", "/send-multi-channel", request, params=params)
        
        if result["status_code"] >= 400:
            raise HTTPException(
                status_code=result["status_code"],
                detail=result["content"].get("detail", "Failed to send notification")
            )
        
        return result["content"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in send_multi_channel_notification proxy: {str(e)}")
        raise HTTPException(status_code=502, detail="Failed to send notification")