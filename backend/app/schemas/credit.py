pythonfrom typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.models.transaction import TransactionType


class CreditBase(BaseModel):
    agent_id: str
    balance: float = 0


class CreditResponse(CreditBase):
    id: str
    agent_name: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    amount: float
    type: TransactionType
    description: Optional[str] = None


class CreditTransaction(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: str
    credit_id: str
    payment_id: Optional[str] = None
    subscription_id: Optional[str] = None
    balance_after: float
    created_by: str
    created_by_name: str
    created_at: datetime

    class Config:
        from_attributes = True