pythonfrom typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import generate_id
from app.models.user import User
from app.models.agent import Agent
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.activity_log import ActivityLog
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.services.credit_service import CreditService
from app.services.notification_service import NotificationService
from app.models.transaction import TransactionType
from app.models.notification import NotificationType


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
        self.credit_service = CreditService(db)
        self.notification_service = NotificationService(db)
    
    def get_payments(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        status: Optional[str] = None
    ) -> List[Payment]:
        """Get all payments with optional status filter"""
        query = self.db.query(Payment)
        
        if status:
            query = query.filter(Payment.status == status)
        
        return query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_agent_payments(
        self,
        agent_id: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Payment]:
        """Get payments for a specific agent"""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            return []
        
        query = self.db.query(Payment).filter(Payment.user_id == agent.user_id)
        
        if status:
            query = query.filter(Payment.status == status)
        
        return query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID"""
        return self.db.query(Payment).filter(Payment.id == payment_id).first()
    
    def create_payment(self, user_id: str, payment_in: PaymentCreate) -> Payment:
        """Create a new payment request"""
        # Create payment
        payment_id = generate_id("PMT")
        payment = Payment(
            id=payment_id,
            user_id=user_id,
            method=payment_in.method,
            amount=payment_in.amount,
            status=PaymentStatus.PENDING,
            description=payment_in.description,
            receipt_image=payment_in.receipt_image
        )
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        # Log activity
        self._log_activity(
            user_id, 
            "create", 
            "payment", 
            payment.id, 
            {
                "amount": payment.amount,
                "method": payment.method.value
            }
        )
        
        return payment
    
    def approve_payment(
        self, 
        payment_id: str, 
        admin_id: str,
        admin_note: Optional[str] = None
    ) -> Payment:
        """Approve a payment and add credit to agent"""
        payment = self.get_payment(payment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        # Only allow approval of pending payments
        if payment.status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot approve {payment.status} payment")
        
        # Update payment status
        payment.status = PaymentStatus.COMPLETED
        payment.approved_by = admin_id
        payment.approved_at = datetime.now()
        
        if admin_note:
            payment.admin_note = admin_note
        
        # Get agent for the user
        agent = self.db.query(Agent).filter(Agent.user_id == payment.user_id).first()
        if not agent:
            raise ValueError("Agent not found for payment user")
        
        # Add credit to agent
        credit = self.credit_service.add_transaction(
            agent_id=agent.id,
            amount=payment.amount,
            transaction_type=TransactionType.DEPOSIT,
            description=f"Payment approved: {payment.id}",
            created_by=admin_id,
            payment_id=payment.id
        )
        
        self.db.commit()
        self.db.refresh(payment)
        
        # Create notification for user
        self.notification_service.create_notification({
            "user_id": payment.user_id,
            "title": "پرداخت تایید شد",
            "message": f"پرداخت شما به مبلغ {payment.amount} تومان تایید شد و به اعتبار شما افزوده شد.",
            "type": NotificationType.PAYMENT,
            "related_id": payment.id,
            "send_to_telegram": True
        })
        
        # Log activity
        self._log_activity(
            admin_id, 
            "approve", 
            "payment", 
            payment.id, 
            {
                "amount": payment.amount,
                "agent_id": agent.id
            }
        )
        
        return payment
    
    def reject_payment(
        self, 
        payment_id: str, 
        admin_id: str,
        admin_note: Optional[str] = None
    ) -> Payment:
        """Reject a payment"""
        payment = self.get_payment(payment_id)
        if not payment:
            raise ValueError("Payment not found")
        
        # Only allow rejection of pending payments
        if payment.status != PaymentStatus.PENDING:
            raise ValueError(f"Cannot reject {payment.status} payment")
        
        # Update payment status
        payment.status = PaymentStatus.REJECTED
        payment.approved_by = admin_id
        payment.approved_at = datetime.now()
        
        if admin_note:
            payment.admin_note = admin_note
        
        self.db.commit()
        self.db.refresh(payment)
        
        # Create notification for user
        self.notification_service.create_notification({
            "user_id": payment.user_id,
            "title": "پرداخت رد شد",
            "message": f"پرداخت شما به مبلغ {payment.amount} تومان رد شد. {admin_note if admin_note else ''}",
            "type": NotificationType.PAYMENT,
            "related_id": payment.id,
            "send_to_telegram": True
        })
        
        # Log activity
        self._log_activity(
            admin_id, 
            "reject", 
            "payment", 
            payment.id, 
            {
                "amount": payment.amount,
                "reason": admin_note
            }
        )
        
        return payment
    
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