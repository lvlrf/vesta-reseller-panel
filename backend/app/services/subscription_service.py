pythonfrom typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import generate_id
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.product import Product, DurationType
from app.models.agent import Agent
from app.models.transaction import Transaction, TransactionType
from app.models.activity_log import ActivityLog
from app.services.credit_service import CreditService
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.credit_service = CreditService(db)
    
    def get_subscriptions(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[str] = None,
        product_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> List[Subscription]:
        """Get all subscriptions with optional filters"""
        query = self.db.query(Subscription)
        
        if status:
            query = query.filter(Subscription.status == status)
        
        if product_id:
            query = query.filter(Subscription.product_id == product_id)
        
        if agent_id:
            query = query.filter(Subscription.agent_id == agent_id)
        
        return query.order_by(Subscription.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    def create_subscription(self, subscription_in: SubscriptionCreate, current_user: User) -> Subscription:
        """Create a new subscription"""
        # Check if product exists
        product = self.db.query(Product).filter(Product.id == subscription_in.product_id).first()
        if not product:
            raise ValueError("Product not found")
        
        # Check if product is active
        if not product.is_active:
            raise ValueError("Product is not active")
        
        # Check if agent exists
        agent = self.db.query(Agent).filter(Agent.id == subscription_in.agent_id).first()
        if not agent:
            raise ValueError("Agent not found")
        
        # Calculate price if not provided
        price = subscription_in.price if subscription_in.price is not None else product.price
        
        # If test subscription, use test duration
        if subscription_in.is_test:
            if not product.has_test_option:
                raise ValueError("Product does not have test option")
            
            # Test subscriptions are free
            price = 0
        
        # Create subscription
        subscription_id = generate_id("SUB")
        subscription = Subscription(
            id=subscription_id,
            product_id=product.id,
            agent_id=agent.id,
            customer_id=agent.user_id,  # For now, set customer to agent's user
            customer_name=subscription_in.customer_name,
            status=SubscriptionStatus.PENDING,
            price=price,
            is_test=subscription_in.is_test,
            customer_note=subscription_in.customer_note
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        
        # Log activity
        self._log_activity(
            current_user.id, 
            "create", 
            "subscription", 
            subscription.id, 
            {
                "product_id": product.id,
                "agent_id": agent.id,
                "price": price,
                "is_test": subscription.is_test
            }
        )
        
        return subscription
    
    def update_subscription(self, subscription_id: str, subscription_in: SubscriptionUpdate) -> Optional[Subscription]:
        """Update a subscription"""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return None
        
        # Only allow updates to pending subscriptions
        if subscription.status != SubscriptionStatus.PENDING:
            raise ValueError("Cannot update a non-pending subscription")
        
        # Update subscription fields
        if subscription_in.customer_name is not None:
            subscription.customer_name = subscription_in.customer_name
        
        if subscription_in.customer_note is not None:
            subscription.customer_note = subscription_in.customer_note
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription
    
    def activate_subscription(self, subscription_id: str, current_user: User) -> Optional[Subscription]:
        """Activate a subscription"""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return None
        
        # Only allow activation of pending subscriptions
        if subscription.status != SubscriptionStatus.PENDING:
            raise ValueError(f"Cannot activate {subscription.status} subscription")
        
        # Get product
        product = subscription.product
        
        # If not a test subscription, deduct from agent's credit
        if not subscription.is_test:
            # Check if agent has enough credit
            agent_credit = self.credit_service.get_agent_credit(subscription.agent_id)
            if not agent_credit or agent_credit.balance < subscription.price:
                raise ValueError("Agent does not have enough credit")
            
            # Deduct from agent's credit
            self.credit_service.add_transaction(
                agent_id=subscription.agent_id,
                amount=-subscription.price,
                transaction_type=TransactionType.WITHDRAWAL,
                description=f"Subscription activation: {product.name} for {subscription.customer_name}",
                created_by=current_user.id,
                subscription_id=subscription.id
            )
        
        # Set start and end dates
        subscription.start_date = datetime.now()
        
        # Calculate end date based on product duration (if not permanent)
        if product.duration_type != DurationType.PERMANENT:
            if product.duration_type == DurationType.DAYS:
                subscription.end_date = subscription.start_date + timedelta(days=product.duration_value)
            elif product.duration_type == DurationType.MONTHS:
                # Simple month calculation (not exact)
                subscription.end_date = subscription.start_date + timedelta(days=product.duration_value * 30)
            elif product.duration_type == DurationType.YEARS:
                subscription.end_date = subscription.start_date + timedelta(days=product.duration_value * 365)
        
        # For test subscriptions, use test duration
        if subscription.is_test:
            subscription.end_date = subscription.start_date + timedelta(days=product.test_duration)
        
        # Update status
        subscription.status = SubscriptionStatus.ACTIVE
        
        self.db.commit()
        self.db.refresh(subscription)
        
        # Log activity
        self._log_activity(
            current_user.id, 
            "activate", 
            "subscription", 
            subscription.id, 
            {
                "start_date": subscription.start_date.isoformat(),
                "end_date": subscription.end_date.isoformat() if subscription.end_date else None
            }
        )
        
        return subscription
    
    def suspend_subscription(self, subscription_id: str, current_user: User) -> Optional[Subscription]:
        """Suspend a subscription"""
        subscription = self.get_subscription(subscription_id)
        if not subscription:
            return None
        
        # Only allow suspension of active subscriptions
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise ValueError(f"Cannot suspend {subscription.status} subscription")
        
        # Update status
        subscription.status = SubscriptionStatus.SUSPENDED
        
        self.db.commit()
        self.db.refresh(subscription)
        
        # Log activity
        self._log_activity(
            current_user.id, 
            "suspend", 
            "subscription", 
            subscription.id, 
            {}
        )
        
        return subscription
    
    def _log_activity(self, user_id: str, action: str, entity_type: str, entity_id: str, details: Dict[str, Any]) -> None:
        """Log user activity"""
        log_id = generate_id("LOG")
        log = ActivityLog(
            id=log_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details
        )
        self.db.add(log)
        self.db.commit()