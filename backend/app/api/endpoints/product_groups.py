pythonfrom typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_admin
from app.models.user import User
from app.schemas.product_group import ProductGroupCreate, ProductGroupResponse, ProductGroupUpdate
from app.services.product_service import ProductService

router = APIRouter()

@router.get("/", response_model=List[ProductGroupResponse])
def get_product_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve product groups.
    """
    product_service = ProductService(db)
    groups = product_service.get_product_groups(skip=skip, limit=limit)
    return groups

@router.post("/", response_model=ProductGroupResponse)
def create_product_group(
    group_in: ProductGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Create new product group.
    """
    product_service = ProductService(db)
    group = product_service.create_product_group(group_in)
    return group

@router.get("/{group_id}", response_model=ProductGroupResponse)
def get_product_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get product group by ID.
    """
    product_service = ProductService(db)
    group = product_service.get_product_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )
    return group

@router.put("/{group_id}", response_model=ProductGroupResponse)
def update_product_group(
    group_id: str,
    group_in: ProductGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Update a product group.
    """
    product_service = ProductService(db)
    group = product_service.get_product_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )
    
    group = product_service.update_product_group(group_id, group_in)
    return group