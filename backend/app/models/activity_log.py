pythonfrom sqlalchemy import Column, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(String, primary_key=True, index=True)  # مثال: LOG-12345
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String)  # عمل انجام شده (مثلاً login, create_subscription)
    entity_type = Column(String, nullable=True)  # نوع موجودیت (مثلاً user, subscription)
    entity_id = Column(String, nullable=True)  # شناسه موجودیت
    details = Column(JSON, nullable=True)  # جزئیات عملیات
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="activity_logs")