pythonfrom typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


@as_declarative()
class Base:
    id: Any
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

# Import all models to ensure they are registered with Base
from app.models.user import User
from app.models.agent import Agent
from app.models.agent_group import AgentGroup
from app.models.product import Product
from app.models.product_group import ProductGroup
from app.models.subscription import Subscription
from app.models.credit import Credit
from app.models.transaction import Transaction
from app.models.payment import Payment
from app.models.notification import Notification
from app.models.setting import Setting
from app.models.activity_log import ActivityLog