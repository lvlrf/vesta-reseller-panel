pythonfrom sqlalchemy import Column, String, Float, Enum, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base

class PaymentMethod(str, enum.Enum):
    CARD_TO_CARD = "card_to_card"  # کارت به کارت
    ONLINE = "online"  # پرداخت آنلاین (برای آینده)

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"  # در انتظار تایید
    COMPLETED = "completed"  # تایید شده
    REJECTED = "rejected"  # رد شده

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, index=True)  # مثال: PMT-12345
    user_id = Column(String, ForeignKey("users.id"))
    method = Column(Enum(PaymentMethod))
    amount = Column(Float)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    receipt_image = Column(String, nullable=True)  # آدرس تصویر رسید (در صورت کارت به کارت)
    description = Column(Text, nullable=True)
    admin_note = Column(Text, nullable=True)  # یادداشت ادمین
    approved_by = Column(String, ForeignKey("users.id"), nullable=True)  # تایید شده توسط
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="payments")
    approver = relationship("User", foreign_keys=[approved_by])
    transaction = relationship("Transaction", back_populates="payment", uselist=False)