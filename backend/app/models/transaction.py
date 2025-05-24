pythonfrom sqlalchemy import Column, String, Float, Enum, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base

class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"  # افزایش اعتبار
    WITHDRAWAL = "withdrawal"  # برداشت اعتبار (خرید اشتراک)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)  # مثال: TRN-12345
    credit_id = Column(String, ForeignKey("credits.id"))
    payment_id = Column(String, ForeignKey("payments.id"), nullable=True)
    subscription_id = Column(String, ForeignKey("subscriptions.id"), nullable=True)
    type = Column(Enum(TransactionType))
    amount = Column(Float)
    balance_after = Column(Float)
    description = Column(Text, nullable=True)
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    credit = relationship("Credit", back_populates="transactions")
    payment = relationship("Payment", back_populates="transaction")
    subscription = relationship("Subscription", back_populates="transaction")