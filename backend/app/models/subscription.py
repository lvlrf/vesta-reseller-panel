pythonfrom sqlalchemy import Column, String, Float, Boolean, Integer, Enum, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base

class SubscriptionStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, index=True)  # مثال: SUB-12345
    product_id = Column(String, ForeignKey("products.id"))
    agent_id = Column(String, ForeignKey("agents.id"))
    customer_id = Column(String, ForeignKey("users.id"))
    customer_name = Column(String)  # نام مشتری نهایی
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING)
    price = Column(Float)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_test = Column(Boolean, default=False)  # آیا نسخه تست است
    customer_note = Column(Text, nullable=True)  # یادداشت نماینده برای مشتری
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="subscriptions")
    agent = relationship("Agent", back_populates="created_subscriptions")
    customer = relationship("User", back_populates="subscriptions")
    transaction = relationship("Transaction", back_populates="subscription", uselist=False)