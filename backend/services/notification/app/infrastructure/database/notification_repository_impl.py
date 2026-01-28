# infrastructure/database/notification_repository_impl.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging


from domain.entities.notification import (
    Notification,
    NotificationType,
    NotificationStatus,
    NotificationPriority
)
from domain.repositories.notification_repository import (
    NotificationRepository
)
from infrastructure.database.supabase_client import SupabaseClient


logger = logging.getLogger(__name__)



class SupabaseNotificationRepository(NotificationRepository):
    """Implementation của NotificationRepository sử dụng Supabase"""


    def __init__(self):
        self.client = SupabaseClient.get_client()
        self.table_name = "notifications"


    def _to_entity(self, data: Dict[str, Any]) -> Notification:
        """Convert database row to Notification entity"""
        return Notification(
            id=data['id'],
            user_id=data['user_id'],
            title=data['title'],
            message=data['message'],
            type=NotificationType(data['type']),
            status=NotificationStatus(data['status']),
            priority=NotificationPriority(data['priority']),
            data=data.get('data'),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            read_at=datetime.fromisoformat(data['read_at'].replace('Z', '+00:00')) if data.get('read_at') else None,
            deleted_at=datetime.fromisoformat(data['deleted_at'].replace('Z', '+00:00')) if data.get('deleted_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')) if data.get('updated_at') else None
        )


    def _to_dict(self, notification: Notification) -> Dict[str, Any]:
        """Convert Notification entity to database dict"""
        return {
            "id": notification.id,
            "user_id": notification.user_id,
            "title": notification.title,
            "message": notification.message,
            "type": notification.type.value,
            "status": notification.status.value,
            "priority": notification.priority.value,
            "data": notification.data,
            "created_at": notification.created_at.isoformat() if notification.created_at else None,
            "read_at": notification.read_at.isoformat() if notification.read_at else None,
            "deleted_at": notification.deleted_at.isoformat() if notification.deleted_at else None,
            "updated_at": notification.updated_at.isoformat() if notification.updated_at else None
        }


    async def create(self, notification: Notification) -> Notification:
        """Tạo thông báo mới"""
        try:
            data = self._to_dict(notification)
            result = self.client.table(self.table_name).insert(data).execute()
            
            if result.data:
                logger.info(f"Created notification {notification.id} for user {notification.user_id}")
                return self._to_entity(result.data[0])
            
            raise Exception("Failed to create notification")
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            raise


    async def get_by_id(self, notification_id: str) -> Optional[Notification]:
        """Lấy thông báo theo ID"""
        try:
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("id", notification_id)\
                .is_("deleted_at", "null")\
                .execute()
            
            if result.data:
                return self._to_entity(result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting notification by id {notification_id}: {str(e)}")
            return None


    async def get_by_user_id(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        type: Optional[NotificationType] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Notification]:
        """Lấy danh sách thông báo của user"""
        try:
            query = self.client.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .is_("deleted_at", "null")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)
            
            if status:
                query = query.eq("status", status.value)
            
            if type:
                query = query.eq("type", type.value)
            
            result = query.execute()
            
            if result.data:
                return [self._to_entity(item) for item in result.data]
            return []
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {str(e)}")
            return []


    async def update(self, notification: Notification) -> Notification:
        """Cập nhật thông báo"""
        try:
            data = self._to_dict(notification)
            data['updated_at'] = datetime.utcnow().isoformat()
            
            result = self.client.table(self.table_name)\
                .update(data)\
                .eq("id", notification.id)\
                .execute()
            
            if result.data:
                logger.info(f"Updated notification {notification.id}")
                return self._to_entity(result.data[0])
            
            raise Exception("Failed to update notification")
        except Exception as e:
            logger.error(f"Error updating notification {notification.id}: {str(e)}")
            raise


    async def delete(self, notification_id: str) -> bool:
        """Xóa thông báo (soft delete)"""
        try:
            result = self.client.table(self.table_name)\
                .update({"deleted_at": datetime.utcnow().isoformat()})\
                .eq("id", notification_id)\
                .execute()
            
            logger.info(f"Soft deleted notification {notification_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {str(e)}")
            return False


    async def mark_as_read(self, notification_id: str) -> bool:
        """Đánh dấu đã đọc"""
        try:
            result = self.client.table(self.table_name)\
                .update({
                    "status": NotificationStatus.READ.value,
                    "read_at": datetime.utcnow().isoformat()
                })\
                .eq("id", notification_id)\
                .execute()
            
            logger.info(f"Marked notification {notification_id} as read")
            return True
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {str(e)}")
            return False


    async def mark_all_as_read(self, user_id: str) -> int:
        """Đánh dấu tất cả đã đọc"""
        try:
            result = self.client.table(self.table_name)\
                .update({
                    "status": NotificationStatus.READ.value,
                    "read_at": datetime.utcnow().isoformat()
                })\
                .eq("user_id", user_id)\
                .eq("status", NotificationStatus.UNREAD.value)\
                .is_("deleted_at", "null")\
                .execute()
            
            count = len(result.data) if result.data else 0
            logger.info(f"Marked {count} notifications as read for user {user_id}")
            return count
        except Exception as e:
            logger.error(f"Error marking all notifications as read for user {user_id}: {str(e)}")
            return 0


    async def get_unread_count(self, user_id: str) -> int:
        """Đếm số thông báo chưa đọc"""
        try:
            result = self.client.table(self.table_name)\
                .select("*", count="exact")\
                .eq("user_id", user_id)\
                .eq("status", NotificationStatus.UNREAD.value)\
                .is_("deleted_at", "null")\
                .execute()
            
            return result.count if result.count else 0
        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {str(e)}")
            return 0


    async def delete_old_notifications(self, days: int = 30) -> int:
        """Xóa thông báo cũ"""
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            result = self.client.table(self.table_name)\
                .update({"deleted_at": datetime.utcnow().isoformat()})\
                .lt("created_at", cutoff_date)\
                .is_("deleted_at", "null")\
                .execute()
            
            count = len(result.data) if result.data else 0
            logger.info(f"Deleted {count} old notifications (older than {days} days)")
            return count
        except Exception as e:
            logger.error(f"Error deleting old notifications: {str(e)}")
            return 0