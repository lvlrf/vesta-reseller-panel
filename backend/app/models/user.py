pythonfrom sqlalchemy import Boolean, Column, String, Integer, Enum, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    AGENT = "agent"

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # مثال: USR-12345
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    mobile = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.AGENT)
    is_active = Column(Boolean, default=True)
    phone = Column(String, nullable=True)
    province = Column(String, nullable=True)
    city = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    business_name = Column(String, nullable=True)
    telegram_id = Column(String, nullable=True)
    whatsapp = Column(String, nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="user", uselist=False)
    activity_logs = relationship("ActivityLog", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="customer")
    notifications = relationship("Notification", back_populates="user")
    payments = relationship("Payment", foreign_keys="[Payment.user_id]", back_populates="user")