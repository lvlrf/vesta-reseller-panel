pythonfrom typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_admin
from app.models.user import User, UserRole
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter()

@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve notifications for the current user.
    """
    notification_service = NotificationService(db)
    notifications = notification_service.get_user_notifications(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    return notifications

@router.post("/", response_model=NotificationResponse)
def create_notification(
    notification_in: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Create a new notification for a user.
    """
    notification_service = NotificationService(db)
    notification = notification_service.create_notification(notification_in)
    
    # Attempt to send to Telegram if configured
    if notification_in.send_to_telegram:
        notification_service.send_notification_to_telegram(notification.id)
    
    return notification

@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Mark a notification as read.
    """
    notification_service = NotificationService(db)
    notification = notification_service.get_notification(notification_id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    
    # Check if the notification belongs to the current user
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    notification = notification_service.mark_as_read(notification_id)
    return notification

@router.post("/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Mark all notifications as read for the current user.
    """
    notification_service = NotificationService(db)
    notification_service.mark_all_as_read(current_user.id)
    return {"message": "All notifications marked as read"}

@router.post("/send-test")
async def send_test_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Send a test notification to the current user.
    """
    notification_service = NotificationService(db)
    
    # Create test notification
    notification_in = NotificationCreate(
        user_id=current_user.id,
        title="Test Notification",
        message="This is a test notification",
        type="SYSTEM",
        send_to_telegram=True
    )
    
    notification = notification_service.create_notification(notification_in)
    
    # Send to Telegram
    success = await notification_service.send_notification_to_telegram(notification.id)
    
    if success:
        return {"message": "Test notification sent successfully"}
    else:
        return {"message": "Notification created, but could not send to Telegram"}