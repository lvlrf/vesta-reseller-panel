pythonfrom datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token, verify_password, generate_otp
from app.schemas.token import Token, TokenPayload
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.services.sms_service import SMSService

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate(username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/request-otp")
async def request_otp(
    mobile: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Request an OTP to login
    """
    auth_service = AuthService(db)
    sms_service = SMSService()
    
    # Generate OTP
    otp = generate_otp()
    
    # Save OTP to database (this is just an example, you'd use a more secure method)
    success = auth_service.save_otp(mobile, otp)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mobile number",
        )
    
    # Send OTP via SMS
    if settings.SMS_API_KEY:  # Only send SMS if API key is configured
        await sms_service.send_otp(mobile, otp)
    
    return {"message": "OTP sent successfully"}

@router.post("/verify-otp", response_model=Token)
def verify_otp(
    mobile: str,
    otp: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify OTP and return access token
    """
    auth_service = AuthService(db)
    user = auth_service.verify_otp(mobile, otp)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=UserResponse)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user
    """
    auth_service = AuthService(db)
    user = auth_service.get_user_by_mobile(user_in.mobile)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this mobile already exists in the system",
        )
    
    user = auth_service.create_user(user_in)
    return user