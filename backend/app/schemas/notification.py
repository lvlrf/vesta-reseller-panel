pythonfrom typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationBase(BaseModel):
    user_id: str
    title: str
    message: str
    type: NotificationType = NotificationType.SYSTEM
    related_id: Optional[str] = None
    send_to_telegram: bool = False


class NotificationCreate(NotificationBase):
    pass


class NotificationResponse(NotificationBase):
    id: str
    is_read: bool
    is_sent_to_telegram: bool
    created_at: datetime

    class Config:
        from_attributes = True