from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.crud.notification import notification_crud
from app.models.user import User
from app.schemas.notification import NotificationResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=List[NotificationResponse],
    summary="Get My Notifications",
    description="Retrieve live status notifications and timeline alerts for current user."
)
def get_my_notifications(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Retrieve notifications for authenticated user."""
    return notification_crud.get_multi_by_user(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )


@router.put(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark Notification as Read",
    description="Mark a specific notification as read."
)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """Mark notification as read."""
    notif = notification_crud.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )
    return notif
