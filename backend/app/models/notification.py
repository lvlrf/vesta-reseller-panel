pythonfrom sqlalchemy import Column, String, Boolean, Enum, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base

class NotificationType(str, enum.Enum):
    SYSTEM = "system"  # اعلان سیستمی
    PAYMENT = "payment"  # اعلان مرتبط با پرداخت

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, index=True)  # مثال: NTF-12345
    user_id = Column(String, ForeignKey("users.id"))
    type = Column(Enum(NotificationType))
    title = Column(String)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    is_sent_to_telegram = Column(Boolean, default=False)
    related_id = Column(String, nullable=True)  # شناسه مرتبط (مثلاً شناسه پرداخت)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="notifications")