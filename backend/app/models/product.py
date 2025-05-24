pythonfrom sqlalchemy import Column, String, Float, Boolean, Integer, Enum, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base import Base

class ProductType(str, enum.Enum):
    API_BASED = "api_based"
    USER_PASSWORD = "user_password"
    LICENSE = "license"

class DurationType(str, enum.Enum):
    DAYS = "days"
    MONTHS = "months"
    YEARS = "years"
    PERMANENT = "permanent"

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)  # مثال: PRD-12345
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    product_type = Column(Enum(ProductType), default=ProductType.API_BASED)
    group_id = Column(String, ForeignKey("product_groups.id"))
    price = Column(Float)
    commission_rate = Column(Float, default=0)  # درصد تخفیف/کمیسیون
    duration_type = Column(Enum(DurationType), default=DurationType.MONTHS)
    duration_value = Column(Integer, default=1)  # تعداد روز/ماه/سال
    is_active = Column(Boolean, default=True)
    has_test_option = Column(Boolean, default=False)  # آیا گزینه تست دارد
    test_duration = Column(Integer, default=0)  # مدت زمان تست به روز
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    group = relationship("ProductGroup", back_populates="products")
    subscriptions = relationship("Subscription", back_populates="product")