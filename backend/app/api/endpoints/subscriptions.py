pythonfrom typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_admin
from app.models.user import User, UserRole
from app.schemas.subscription import (
    SubscriptionCreate, 
    SubscriptionResponse, 
    SubscriptionUpdate
)
from app.services.subscription_service import SubscriptionService

router = APIRouter()

@router.get("/", response_model=List[SubscriptionResponse])
def get_subscriptions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    product_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve subscriptions.
    """
    subscription_service = SubscriptionService(db)
    
    # If user is agent, only show their subscriptions
    if current_user.role == UserRole.AGENT:
        agent_id = current_user.agent.id
    
    subscriptions = subscription_service.get_subscriptions(
        skip=skip, 
        limit=limit, 
        status=status,
        product_id=product_id,
        agent_id=agent_id
    )
    return subscriptions

@router.post("/", response_model=SubscriptionResponse)
def create_subscription(
    subscription_in: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new subscription.
    """
    subscription_service = SubscriptionService(db)
    
    # If user is agent, force agent_id to be current user's agent id
    if current_user.role == UserRole.AGENT:
        subscription_in.agent_id = current_user.agent.id
    
    subscription = subscription_service.create_subscription(subscription_in, current_user)
    return subscription

@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get subscription by ID.
    """
    subscription_service = SubscriptionService(db)
    subscription = subscription_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    # Check if user has access to this subscription
    if (current_user.role == UserRole.AGENT and 
        current_user.agent.id != subscription.agent_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return subscription

@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: str,
    subscription_in: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update a subscription.
    """
    subscription_service = SubscriptionService(db)
    subscription = subscription_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    # Check if user has access to update this subscription
    if (current_user.role == UserRole.AGENT and 
        current_user.agent.id != subscription.agent_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    subscription = subscription_service.update_subscription(subscription_id, subscription_in)
    return subscription

@router.post("/{subscription_id}/activate", response_model=SubscriptionResponse)
def activate_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Activate a subscription.
    """
    subscription_service = SubscriptionService(db)
    subscription = subscription_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    # Check if user has access to activate this subscription
    if (current_user.role == UserRole.AGENT and 
        current_user.agent.id != subscription.agent_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    try:
        subscription = subscription_service.activate_subscription(subscription_id, current_user)
        return subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post("/{subscription_id}/suspend", response_model=SubscriptionResponse)
def suspend_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Suspend a subscription.
    """
    subscription_service = SubscriptionService(db)
    subscription = subscription_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    
    # Check if user has access to suspend this subscription
    # Only admins can suspend subscriptions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    try:
        subscription = subscription_service.suspend_subscription(subscription_id, current_user)
        return subscription
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )