pythonfrom typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import generate_id
from app.models.agent import Agent
from app.models.credit import Credit
from app.models.transaction import Transaction, TransactionType
from app.models.payment import Payment
from app.models.subscription import Subscription


class CreditService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_credits(self) -> List[Credit]:
        """Get all credits"""
        return self.db.query(Credit).all()
    
    def get_agent_credit(self, agent_id: str) -> Optional[Credit]:
        """Get credit for a specific agent"""
        credit = self.db.query(Credit).filter(Credit.agent_id == agent_id).first()
        
        # Create credit record if not exists
        if not credit:
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                return None
            
            credit_id = generate_id("CRD")
            credit = Credit(id=credit_id, agent_id=agent_id, balance=0)
            self.db.add(credit)
            self.db.commit()
            self.db.refresh(credit)
        
        return credit
    
    def add_transaction(
        self, 
        agent_id: str, 
        amount: float, 
        transaction_type: TransactionType,
        description: Optional[str] = None,
        created_by: str = None,
        payment_id: Optional[str] = None,
        subscription_id: Optional[str] = None
    ) -> Credit:
        """Add a transaction (deposit/withdrawal) for an agent"""
        credit = self.get_agent_credit(agent_id)
        if not credit:
            raise ValueError("Credit not found for agent")
        
        # Calculate new balance
        new_balance = credit.balance + amount
        
        # Don't allow negative balance for withdrawal
        if transaction_type == TransactionType.WITHDRAWAL and new_balance < 0:
            raise ValueError("Not enough credit")
        
        # Update credit balance
        credit.balance = new_balance
        
        # Create transaction record
        transaction_id = generate_id("TRN")
        transaction = Transaction(
            id=transaction_id,
            credit_id=credit.id,
            type=transaction_type,
            amount=amount,
            balance_after=new_balance,
            description=description,
            payment_id=payment_id,
            subscription_id=subscription_id,
            created_by=created_by
        )
        self.db.add(transaction)
        
        self.db.commit()
        self.db.refresh(credit)
        
        return credit
    
    def get_agent_transactions(
        self, 
        agent_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Transaction]:
        """Get transactions for a specific agent"""
        credit = self.get_agent_credit(agent_id)
        if not credit:
            return []
        
        return self.db.query(Transaction).filter(
            Transaction.credit_id == credit.id
        ).order_by(
            Transaction.created_at.desc()
        ).offset(skip).limit(limit).all()