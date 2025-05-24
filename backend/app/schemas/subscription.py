pythonfrom typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.models.subscription import SubscriptionStatus
from app.schemas.product import ProductResponse


class SubscriptionBase(BaseModel):
    product_id: str
    agent_id: str
    customer_name: str
    price: Optional[float] = None
    is_test: bool = False
    customer_note: Optional[str] = None


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_note: Optional[str] = None


class SubscriptionResponse(BaseModel):
    id: str
    product: ProductResponse
    agent_id: str
    agent_name: str
    customer_name: str
    status: SubscriptionStatus
    price: float
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_test: bool
    customer_note: Optional[str] = None
    days_left: Optional[int] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True