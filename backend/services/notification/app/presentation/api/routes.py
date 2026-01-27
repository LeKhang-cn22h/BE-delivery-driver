# presentation/api/routes.py
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
    get_send_multi_channel_notification_use_case
)


router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])



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
        result = await use_case.execute(
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            type=NotificationType(notification.type.value),
            priority=notification.priority,
            data=notification.data
        )
        return NotificationResponse(**result.to_dict())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
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
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notifications: {str(e)}"
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification: {str(e)}"
        )



@router.put(
    "/{notification_id}/read",
    response_model=SuccessResponse,
    summary="Đánh dấu đã đọc",
    description="Đánh dấu một thông báo đã được đọc"
)
async def mark_as_read(
    notification_id: str,
    use_case: MarkAsReadUseCase = Depends(get_mark_as_read_use_case)
):
    """Đánh dấu đã đọc"""
    try:
        result = await use_case.execute(notification_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return SuccessResponse(
            message="Notification marked as read",
            data={"notification_id": notification_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark as read: {str(e)}"
        )



@router.put(
    "/read-all",
    response_model=SuccessResponse,
    summary="Đánh dấu tất cả đã đọc",
    description="Đánh dấu tất cả thông báo của user đã được đọc"
)
async def mark_all_as_read(
    user_id: str = Query(..., description="ID của user"),
    use_case: MarkAllAsReadUseCase = Depends(get_mark_all_as_read_use_case)
):
    """Đánh dấu tất cả đã đọc"""
    try:
        count = await use_case.execute(user_id)
        return SuccessResponse(
            message=f"Marked {count} notifications as read",
            data={"count": count}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark all as read: {str(e)}"
        )



@router.delete(
    "/{notification_id}",
    response_model=SuccessResponse,
    summary="Xóa thông báo",
    description="Xóa một thông báo (soft delete)"
)
async def delete_notification(
    notification_id: str,
    use_case: DeleteNotificationUseCase = Depends(get_delete_notification_use_case)
):
    """Xóa thông báo"""
    try:
        result = await use_case.execute(notification_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return SuccessResponse(
            message="Notification deleted",
            data={"notification_id": notification_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
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
        count = await use_case.execute(user_id)
        return {"user_id": user_id, "unread_count": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread count: {str(e)}"
        )


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
    user_email: Optional[str] = Query(None, description="Email của customer (nếu là customer)"),
    device_token: Optional[str] = Query(None, description="FCM token của shipper (nếu là shipper)"),
    use_case: SendMultiChannelNotificationUseCase = Depends(get_send_multi_channel_notification_use_case)
):
    """
    Gửi thông báo qua email hoặc push notification

    - Nếu user_type = 'customer' → Gửi email
    - Nếu user_type = 'shipper' → Gửi push notification (FCM)

    Examples:

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

        return SuccessResponse(
            message="Notification sent successfully",
            data={
                "notification_id": notification.id,
                "user_id": user_id,
                "user_type": user_type,
                "notification_type": notification_type
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )