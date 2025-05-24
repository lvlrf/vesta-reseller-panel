pythonfrom typing import Optional, List
from pydantic import BaseModel


class ProductGroupBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProductGroupCreate(ProductGroupBase):
    pass


class ProductGroupUpdate(ProductGroupBase):
    pass


class ProductGroupResponse(ProductGroupBase):
    id: str
    product_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True