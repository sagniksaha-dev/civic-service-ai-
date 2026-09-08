from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    """Base schema for notifications."""
    title: str = Field(..., max_length=200)
    message: str
    notification_type: str = Field(default="system", max_length=50)
    reference_id: Optional[str] = None


class NotificationCreate(NotificationBase):
    """Schema to create a notification log entry."""
    user_id: int


class NotificationResponse(NotificationBase):
    """Schema for notification response."""
    id: int
    user_id: int
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
