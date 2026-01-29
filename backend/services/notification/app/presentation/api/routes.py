# presentation/api/routes.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional

from presentation.schemas.notification_schema import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationUpdate,
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationPreferenceResponse,
    SuccessResponse,
    NotificationTypeEnum,
    NotificationStatusEnum
)
from application.use_cases.notification_use_cases import (
    CreateNotificationUseCase,
    GetNotificationsUseCase,
    GetNotificationByIdUseCase,
    MarkAsReadUseCase,
    MarkAllAsReadUseCase,
    DeleteNotificationUseCase,
    GetUnreadCountUseCase,
    SendMultiChannelNotificationUseCase
)
from domain.entities.notification import NotificationType, NotificationStatus, NotificationPriority
from presentation.api.dependencies import (
    get_create_notification_use_case,
    get_notifications_use_case,
    get_notification_by_id_use_case,
    get_mark_as_read_use_case,
    get_mark_all_as_read_use_case,
    get_delete_notification_use_case,
    get_unread_count_use_case,
    get_send_multi_channel_notification_use_case,
    get_save_fcm_token_use_case,
    get_remove_fcm_token_use_case
)
from pydantic import BaseModel
from application.use_cases.user_use_cases import (
    SaveFCMTokenUseCase,
    RemoveFCMTokenUseCase
)

# Logger setup
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

# SCHEMAS
class FCMTokenRequest(BaseModel):
    fcm_token: str


class FCMTokenResponse(BaseModel):
    user_id: str
    fcm_token: str

# FCM TOKEN ENDPOINTS
@router.post(
    "/users/{user_id}/fcm",
    response_model=FCMTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Lưu FCM token của user",
    description="Lưu Firebase Cloud Messaging token cho thiết bị của user"
)
async def save_fcm_token(
    user_id: str,
    request: FCMTokenRequest,
    use_case: SaveFCMTokenUseCase = Depends(get_save_fcm_token_use_case)
):
    """Lưu FCM token của user"""
    try:
        logger.info(f"Saving FCM token for user {user_id}")
        result = await use_case.execute(user_id, request.fcm_token)
        logger.info(f"FCM token saved successfully for user {user_id}")
        return FCMTokenResponse(
            user_id=str(result.id),  # Convert UUID to string
            fcm_token=result.fcm_token
        )
    except ValueError as e:
        logger.error(f"Invalid input for user {user_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        logger.error(f"Error saving FCM token for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save FCM token")


@router.delete(
    "/users/{user_id}/fcm",
    status_code=status.HTTP_200_OK,
    summary="Xóa FCM token của user",
    description="Xóa Firebase Cloud Messaging token khi user logout"
)
async def remove_fcm_token(
    user_id: str,
    use_case: RemoveFCMTokenUseCase = Depends(get_remove_fcm_token_use_case)
):
    """Xóa FCM token khi user logout"""
    try:
        logger.info(f"Removing FCM token for user {user_id}")
        result = await use_case.execute(user_id)
        logger.info(f"FCM token removed successfully for user {user_id}")
        return {
            "user_id": str(result.id),  # Convert UUID to string
            "message": "FCM token removed"
        }
    except ValueError as e:
        logger.error(f"User not found {user_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Error removing FCM token for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove FCM token")


# NOTIFICATION ENDPOINTS
@router.post(
    "/",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo thông báo mới",
    description="Tạo một thông báo mới cho user"
)
async def create_notification(
    notification: NotificationCreate,
    use_case: CreateNotificationUseCase = Depends(get_create_notification_use_case)
):
    """Tạo thông báo mới"""
    try:
        logger.info(f"Creating notification for user {notification.user_id}")
        result = await use_case.execute(
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            type=NotificationType(notification.type.value),
            priority=notification.priority,
            data=notification.data
        )
        logger.info(f"Notification created successfully: {result.id}")
        return NotificationResponse(**result.to_dict())
    except ValueError as e:
        logger.error(f"Invalid notification data: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="Lấy danh sách thông báo",
    description="Lấy danh sách thông báo của user với filter và phân trang"
)
async def get_notifications(
    user_id: str = Query(..., description="ID của user"),
    status: Optional[NotificationStatusEnum] = Query(None, description="Lọc theo trạng thái"),
    type: Optional[NotificationTypeEnum] = Query(None, description="Lọc theo loại"),
    page: int = Query(1, ge=1, description="Số trang"),
    page_size: int = Query(20, ge=1, le=100, description="Số lượng mỗi trang"),
    use_case: GetNotificationsUseCase = Depends(get_notifications_use_case),
    unread_count_use_case: GetUnreadCountUseCase = Depends(get_unread_count_use_case)
):
    """Lấy danh sách thông báo"""
    try:
        logger.info(f"Fetching notifications for user {user_id}, page {page}")
        offset = (page - 1) * page_size
        
        # Convert enum to domain enum nếu có
        status_filter = NotificationStatus(status.value) if status else None
        type_filter = NotificationType(type.value) if type else None
        
        notifications = await use_case.execute(
            user_id=user_id,
            status=status_filter,
            type=type_filter,
            limit=page_size,
            offset=offset
        )
        
        unread_count = await unread_count_use_case.execute(user_id)
        
        return NotificationListResponse(
            notifications=[NotificationResponse(**n.to_dict()) for n in notifications],
            total=len(notifications),
            unread_count=unread_count,
            page=page,
            page_size=page_size
        )
    except ValueError as e:
        logger.error(f"Invalid filter parameters: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )


@router.get(
    "/unread/count",
    response_model=dict,
    summary="Đếm số thông báo chưa đọc",
    description="Lấy số lượng thông báo chưa đọc của user"
)
async def get_unread_count(
    user_id: str = Query(..., description="ID của user"),
    use_case: GetUnreadCountUseCase = Depends(get_unread_count_use_case)
):
    """Đếm số thông báo chưa đọc"""
    try:
        logger.info(f"Fetching unread count for user {user_id}")
        count = await use_case.execute(user_id)
        return {"user_id": user_id, "unread_count": count}
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread count"
        )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="Lấy thông báo theo ID",
    description="Lấy chi tiết một thông báo"
)
async def get_notification(
    notification_id: str,
    use_case: GetNotificationByIdUseCase = Depends(get_notification_by_id_use_case)
):
    """Lấy thông báo theo ID"""
    try:
        logger.info(f"Fetching notification {notification_id}")
        notification = await use_case.execute(notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return NotificationResponse(**notification.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching notification {notification_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification"
        )


@router.put(
    "/{notification_id}/read",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Đánh dấu đã đọc",
    description="Đánh dấu một thông báo đã được đọc"
)
async def mark_as_read(
    notification_id: str,
    use_case: MarkAsReadUseCase = Depends(get_mark_as_read_use_case)
):
    """Đánh dấu đã đọc"""
    try:
        logger.info(f"Marking notification {notification_id} as read")
        result = await use_case.execute(notification_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        logger.info(f"Notification {notification_id} marked as read")
        return SuccessResponse(
            message="Notification marked as read",
            data={"notification_id": notification_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark as read"
        )


@router.put(
    "/read-all",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Đánh dấu tất cả đã đọc",
    description="Đánh dấu tất cả thông báo của user đã được đọc"
)
async def mark_all_as_read(
    user_id: str = Query(..., description="ID của user"),
    use_case: MarkAllAsReadUseCase = Depends(get_mark_all_as_read_use_case)
):
    """Đánh dấu tất cả đã đọc"""
    try:
        logger.info(f"Marking all notifications as read for user {user_id}")
        count = await use_case.execute(user_id)
        logger.info(f"Marked {count} notifications as read for user {user_id}")
        return SuccessResponse(
            message=f"Marked {count} notifications as read",
            data={"count": count}
        )
    except Exception as e:
        logger.error(f"Error marking all as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all as read"
        )


@router.delete(
    "/{notification_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Xóa thông báo",
    description="Xóa một thông báo (soft delete)"
)
async def delete_notification(
    notification_id: str,
    use_case: DeleteNotificationUseCase = Depends(get_delete_notification_use_case)
):
    """Xóa thông báo"""
    try:
        logger.info(f"Deleting notification {notification_id}")
        result = await use_case.execute(notification_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        logger.info(f"Notification {notification_id} deleted")
        return SuccessResponse(
            message="Notification deleted",
            data={"notification_id": notification_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )


# MULTI-CHANNEL NOTIFICATION ENDPOINT
@router.post(
    "/send-multi-channel",
    response_model=SuccessResponse,
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
    user_email: str | None = Query(None, description="Email của customer (nếu là customer)"),
    device_token: str | None = Query(None, description="FCM token của shipper (nếu là shipper)"),
    use_case: SendMultiChannelNotificationUseCase = Depends(get_send_multi_channel_notification_use_case)
):
    """
    Gửi thông báo qua email hoặc push notification

    - Nếu user_type = 'customer' → Gửi email
    - Nếu user_type = 'shipper' → Gửi push notification (FCM)

    **Examples:**

    1. Gửi email cho customer:
    ```
    POST /api/v1/notifications/send-multi-channel?user_id=cust_123&user_type=customer&title=Đơn hàng xác nhận&body=Đơn hàng #12345 đã xác nhận&user_email=customer@example.com&notification_type=order
    ```

    2. Gửi push cho shipper:
    ```
    POST /api/v1/notifications/send-multi-channel?user_id=ship_456&user_type=shipper&title=Đơn hàng mới&body=Bạn có 1 đơn hàng&device_token=eXfXr7T...&notification_type=delivery
    ```
    """
    try:
        logger.info(f"Sending {user_type} notification to user {user_id}")
        
        # Validate user_type
        if user_type not in ["customer", "shipper"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_type must be 'customer' or 'shipper'"
            )

        # Validate required fields dựa trên user_type
        if user_type == "customer" and not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_email is required for customer notifications"
            )

        if user_type == "shipper" and not device_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="device_token is required for shipper notifications"
            )

        # Execute use case
        notification = await use_case.execute(
            user_id=user_id,
            user_type=user_type,
            title=title,
            body=body,
            notification_type=NotificationType(notification_type.upper()),
            priority=NotificationPriority.NORMAL,
            user_email=user_email,
            device_token=device_token,
            data=None
        )

        logger.info(f"Notification sent successfully to {user_type}: {notification.id}")
        return SuccessResponse(
            message="Notification sent successfully",
            data={
                "notification_id": str(notification.id),  # Convert UUID to string
                "user_id": user_id,
                "user_type": user_type,
                "notification_type": notification_type
            }
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid notification type: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        logger.error(f"Error sending multi-channel notification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send notification"
        )