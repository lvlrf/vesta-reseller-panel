pythonfrom typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_admin
from app.models.user import User, UserRole
from app.schemas.credit import CreditResponse, CreditTransaction
from app.services.credit_service import CreditService

router = APIRouter()

@router.get("/", response_model=List[CreditResponse])
def get_credits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve credits for the current user or all users (admin only).
    """
    credit_service = CreditService(db)
    
    if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        credits = credit_service.get_all_credits()
    else:
        if not current_user.agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found for current user",
            )
        credits = [credit_service.get_agent_credit(current_user.agent.id)]
        
    return credits

@router.get("/{agent_id}", response_model=CreditResponse)
def get_agent_credit(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get credit for a specific agent.
    """
    # Check permissions: Only admins or the agent itself can see the credit
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if not current_user.agent or current_user.agent.id != agent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    credit_service = CreditService(db)
    credit = credit_service.get_agent_credit(agent_id)
    if not credit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit not found for the agent",
        )
    
    return credit

@router.post("/{agent_id}/transactions", response_model=CreditResponse)
def add_credit_transaction(
    agent_id: str,
    transaction: CreditTransaction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Add a credit transaction (deposit/withdrawal) for an agent.
    Only admins can add transactions.
    """
    credit_service = CreditService(db)
    
    try:
        credit = credit_service.add_transaction(
            agent_id=agent_id,
            amount=transaction.amount,
            transaction_type=transaction.type,
            description=transaction.description,
            created_by=current_user.id
        )
        return credit
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.get("/{agent_id}/transactions")
def get_credit_transactions(
    agent_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get credit transactions for a specific agent.
    """
    # Check permissions: Only admins or the agent itself can see the transactions
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if not current_user.agent or current_user.agent.id != agent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    credit_service = CreditService(db)
    transactions = credit_service.get_agent_transactions(
        agent_id=agent_id,
        skip=skip,
        limit=limit
    )
    
    return transactions