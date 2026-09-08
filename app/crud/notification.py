from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.notification import Notification
from app.schemas.notification import NotificationCreate


class CRUDNotification:
    """CRUD operations for user notifications and timeline events."""

    def create(self, db: Session, obj_in: NotificationCreate) -> Notification:
        """Create a notification record."""
        notification = Notification(
            user_id=obj_in.user_id,
            title=obj_in.title,
            message=obj_in.message,
            notification_type=obj_in.notification_type,
            reference_id=obj_in.reference_id,
            is_read=False
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def get_multi_by_user(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """Fetch notifications for a user."""
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    def mark_as_read(self, db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        """Mark notification as read."""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
        notification = db.execute(stmt).scalar_one_or_none()
        if notification:
            notification.is_read = True
            db.commit()
            db.refresh(notification)
        return notification


notification_crud = CRUDNotification()
