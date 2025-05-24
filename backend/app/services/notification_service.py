pythonfrom typing import List, Optional, Dict, Any
import httpx
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import generate_id
from app.core.config import settings
from app.models.notification import Notification, NotificationType
from app.models.user import User


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_notifications(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID"""
        return self.db.query(Notification).filter(Notification.id == notification_id).first()
    
    def create_notification(self, notification_data: Dict[str, Any]) -> Notification:
        """Create a new notification"""
        # Check if user exists
        user = self.db.query(User).filter(User.id == notification_data["user_id"]).first()
        if not user:
            raise ValueError("User not found")
        
        # Create notification
        notification_id = generate_id("NTF")
        notification = Notification(
            id=notification_id,
            user_id=notification_data["user_id"],
            title=notification_data["title"],
            message=notification_data["message"],
            type=notification_data["type"],
            is_read=False,
            is_sent_to_telegram=False,
            related_id=notification_data.get("related_id")
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        return notification
    
    def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        """Mark a notification as read"""
        notification = self.get_notification(notification_id)
        if not notification:
            return None
        
        notification.is_read = True
        self.db.commit()
        self.db.refresh(notification)
        
        return notification
    
    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        result = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True})
        
        self.db.commit()
        return result
    
    async def send_notification_to_telegram(self, notification_id: str) -> bool:
        """Send notification to Telegram"""
        notification = self.get_notification(notification_id)
        if not notification:
            return False
        
        # Check if user has Telegram ID
        user = self.db.query(User).filter(User.id == notification.user_id).first()
        if not user or not user.telegram_id:
            return False
        
        # Check if Telegram bot token is configured
        if not settings.TELEGRAM_BOT_TOKEN:
            return False
        
        try:
            # Send message to Telegram
            telegram_api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            message_text = f"*{notification.title}*\n\n{notification.message}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    telegram_api_url,
                    json={
                        "chat_id": user.telegram_id,
                        "text": message_text,
                        "parse_mode": "Markdown"
                    }
                )
                
                if response.status_code == 200:
                    # Mark as sent
                    notification.is_sent_to_telegram = True
                    self.db.commit()
                    return True
            
            return False
        except Exception as e:
            print(f"Error sending Telegram notification: {e}")
            return False