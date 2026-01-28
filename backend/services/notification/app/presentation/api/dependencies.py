from functools import lru_cache
from fastapi import Depends


from domain.repositories.notification_repository import NotificationRepository
from infrastructure.database.notification_repository_impl import (
    SupabaseNotificationRepository
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
from infrastructure.database.user_repository_impl import SupabaseUserRepository
from application.use_cases.user_use_cases import (
    SaveFCMTokenUseCase,
    RemoveFCMTokenUseCase
)


def get_save_fcm_token_use_case() -> SaveFCMTokenUseCase:
    """Inject SaveFCMTokenUseCase"""
    user_repo = SupabaseUserRepository()
    return SaveFCMTokenUseCase(user_repo)


def get_remove_fcm_token_use_case() -> RemoveFCMTokenUseCase:
    """Inject RemoveFCMTokenUseCase"""
    user_repo = SupabaseUserRepository()
    return RemoveFCMTokenUseCase(user_repo)


# Repository Instances
@lru_cache()
def get_notification_repository() -> NotificationRepository:
    """Get notification repository instance"""
    return SupabaseNotificationRepository()


# Use Case Dependencies
def get_create_notification_use_case(
    repository: NotificationRepository = Depends(get_notification_repository)
) -> CreateNotificationUseCase:
    """Get CreateNotificationUseCase instance"""
    return CreateNotificationUseCase(repository)



def get_notifications_use_case(
    repository: NotificationRepository = Depends(get_notification_repository)
) -> GetNotificationsUseCase:
    """Get GetNotificationsUseCase instance"""
    return GetNotificationsUseCase(repository)



def get_notification_by_id_use_case(
    repository: NotificationRepository = Depends(get_notification_repository)
) -> GetNotificationByIdUseCase:
    """Get GetNotificationByIdUseCase instance"""
    return GetNotificationByIdUseCase(repository)



def get_mark_as_read_use_case(
    repository: NotificationRepository = Depends(get_notification_repository)
) -> MarkAsReadUseCase:
    """Get MarkAsReadUseCase instance"""
    return MarkAsReadUseCase(repository)



def get_mark_all_as_read_use_case(
    repository: NotificationRepository = Depends(get_notification_repository)
) -> MarkAllAsReadUseCase:
    """Get MarkAllAsReadUseCase instance"""
    return MarkAllAsReadUseCase(repository)



def get_delete_notification_use_case(
    repository: NotificationRepository = Depends(get_notification_repository)
) -> DeleteNotificationUseCase:
    """Get DeleteNotificationUseCase instance"""
    return DeleteNotificationUseCase(repository)



def get_unread_count_use_case(
    repository: NotificationRepository = Depends(get_notification_repository)
) -> GetUnreadCountUseCase:
    """Get GetUnreadCountUseCase instance"""
    return GetUnreadCountUseCase(repository)



def get_send_multi_channel_notification_use_case(
    repository: NotificationRepository = Depends(get_notification_repository)
) -> SendMultiChannelNotificationUseCase:
    """Get SendMultiChannelNotificationUseCase instance (Microservice version)"""
    return SendMultiChannelNotificationUseCase(repository=repository)
