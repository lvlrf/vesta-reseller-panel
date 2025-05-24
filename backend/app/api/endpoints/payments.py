pythonfrom typing import Any, List, Optional
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_admin
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.payment import (
    PaymentCreate, 
    PaymentResponse, 
    PaymentUpdate,
    PaymentApproveReject
)
from app.services.payment_service import PaymentService

router = APIRouter()

@router.get("/", response_model=List[PaymentResponse])
def get_payments(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Retrieve payments.
    """
    payment_service = PaymentService(db)
    
    # If user is an agent, only get their payments
    if current_user.role == UserRole.AGENT:
        if not current_user.agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found for current user",
            )
        payments = payment_service.get_agent_payments(
            agent_id=current_user.agent.id,
            skip=skip,
            limit=limit,
            status=status
        )
    else:
        # Admins can see all payments
        payments = payment_service.get_payments(
            skip=skip,
            limit=limit,
            status=status
        )
    
    return payments

@router.post("/", response_model=PaymentResponse)
async def create_payment(
    amount: float = Form(...),
    description: Optional[str] = Form(None),
    receipt_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new payment request (card-to-card).
    """
    if not current_user.agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found for current user",
        )
    
    payment_service = PaymentService(db)
    
    # If receipt image is provided, save it
    receipt_image_path = None
    if receipt_image:
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(settings.UPLOAD_DIR, "receipts")
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save the file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(receipt_image.filename)[1]
        filename = f"{current_user.id}_{timestamp}{file_extension}"
        file_path = os.path.join(uploads_dir, filename)
        
        contents = await receipt_image.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        receipt_image_path = f"/uploads/receipts/{filename}"
    
    # Create payment request
    payment_in = PaymentCreate(
        amount=amount,
        description=description,
        receipt_image=receipt_image_path,
    )
    
    payment = payment_service.create_payment(
        user_id=current_user.id,
        payment_in=payment_in
    )
    
    return payment

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get payment by ID.
    """
    payment_service = PaymentService(db)
    payment = payment_service.get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    # Check permissions: Only admins or the payment owner can see the payment
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        if payment.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    
    return payment

@router.post("/{payment_id}/approve", response_model=PaymentResponse)
def approve_payment(
    payment_id: str,
    approval: PaymentApproveReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Approve a payment.
    """
    payment_service = PaymentService(db)
    payment = payment_service.get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    try:
        payment = payment_service.approve_payment(
            payment_id=payment_id,
            admin_id=current_user.id,
            admin_note=approval.admin_note
        )
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@router.post("/{payment_id}/reject", response_model=PaymentResponse)
def reject_payment(
    payment_id: str,
    rejection: PaymentApproveReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Reject a payment.
    """
    payment_service = PaymentService(db)
    payment = payment_service.get_payment(payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    
    try:
        payment = payment_service.reject_payment(
            payment_id=payment_id,
            admin_id=current_user.id,
            admin_note=rejection.admin_note
        )
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )