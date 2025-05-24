pythonfrom typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.models.payment import PaymentMethod, PaymentStatus


class PaymentBase(BaseModel):
    amount: float
    method: PaymentMethod = PaymentMethod.CARD_TO_CARD
    description: Optional[str] = None
    receipt_image: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    description: Optional[str] = None


class PaymentApproveReject(BaseModel):
    admin_note: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: str
    user_id: str
    user_name: str
    status: PaymentStatus
    admin_note: Optional[str] = None
    approved_by: Optional[str] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True