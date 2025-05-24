pythonfrom typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import generate_id
from app.models.product import Product, ProductType, DurationType
from app.models.product_group import ProductGroup
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.product_group import ProductGroupCreate, ProductGroupUpdate


class ProductService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_products(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        group_id: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Product]:
        """Get all products with optional filters"""
        query = self.db.query(Product)
        
        if group_id:
            query = query.filter(Product.group_id == group_id)
        
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID"""
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def create_product(self, product_in: ProductCreate) -> Product:
        """Create a new product"""
        # Check if product group exists
        group = self.get_product_group(product_in.group_id)
        if not group:
            raise ValueError("Product group not found")
        
        # Create product
        product_id = generate_id("PRD")
        product_data = product_in.dict()
        product_data["id"] = product_id
        
        product = Product(**product_data)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def update_product(self, product_id: str, product_in: ProductUpdate) -> Optional[Product]:
        """Update a product"""
        product = self.get_product(product_id)
        if not product:
            return None
        
        # Check if product group exists if changing
        if product_in.group_id is not None and product_in.group_id != product.group_id:
            group = self.get_product_group(product_in.group_id)
            if not group:
                raise ValueError("Product group not found")
        
        # Update product fields
        update_data = product_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def activate_product(self, product_id: str) -> Optional[Product]:
        """Activate a product"""
        product = self.get_product(product_id)
        if not product:
            return None
        
        product.is_active = True
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def deactivate_product(self, product_id: str) -> Optional[Product]:
        """Deactivate a product"""
        product = self.get_product(product_id)
        if not product:
            return None
        
        product.is_active = False
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    # Product Group methods
    def get_product_groups(self, skip: int = 0, limit: int = 100) -> List[ProductGroup]:
        """Get all product groups"""
        return self.db.query(ProductGroup).offset(skip).limit(limit).all()
    
    def get_product_group(self, group_id: str) -> Optional[ProductGroup]:
        """Get product group by ID"""
        return self.db.query(ProductGroup).filter(ProductGroup.id == group_id).first()
    
    def create_product_group(self, group_in: ProductGroupCreate) -> ProductGroup:
        """Create a new product group"""
        group_id = generate_id("PGP")
        group = ProductGroup(
            id=group_id,
            name=group_in.name,
            description=group_in.description
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        
        return group
    
    def update_product_group(self, group_id: str, group_in: ProductGroupUpdate) -> Optional[ProductGroup]:
        """Update a product group"""
        group = self.get_product_group(group_id)
        if not group:
            return None
        
        group.name = group_in.name
        group.description = group_in.description
        
        self.db.commit()
        self.db.refresh(group)
        
        return group