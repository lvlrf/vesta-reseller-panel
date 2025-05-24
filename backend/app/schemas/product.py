pythonfrom typing import Optional, List
from pydantic import BaseModel

from app.models.product import ProductType, DurationType


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    product_type: ProductType = ProductType.API_BASED
    group_id: str
    price: float
    commission_rate: float = 0
    duration_type: DurationType = DurationType.MONTHS
    duration_value: int = 1
    is_active: bool = True
    has_test_option: bool = False
    test_duration: int = 0


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    name: Optional[str] = None
    group_id: Optional[str] = None
    price: Optional[float] = None
    commission_rate: Optional[float] = None
    duration_type: Optional[DurationType] = None
    duration_value: Optional[int] = None


class ProductResponse(ProductBase):
    id: str
    group_name: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True