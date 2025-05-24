# backend/app/services/auth_service.py (بهبود یافته)
from typing import Optional, Dict, Any
from datetime import datetime
import re

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import get_password_hash, verify_password, generate_id
from app.core.utils import validate_mobile, format_mobile
from app.core.exceptions import VestaException
from app.models.user import User, UserRole
from app.models.agent import Agent
from app.models.credit import Credit
from app.models.activity_log import ActivityLog
from app.schemas.user import UserCreate, UserUpdate
from app.services.otp_service import OTPService

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.otp_service = OTPService()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_mobile(self, mobile: str) -> Optional[User]:
        # Format mobile number
        mobile = format_mobile(mobile)
        if not mobile:
            return None
        
        return self.db.query(User).filter(User.mobile == mobile).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        # Check if username is email, mobile or username
        if '@' in username:
            user = self.get_user_by_email(username)
        elif validate_mobile(username):
            user = self.get_user_by_mobile(username)
        else:
            user = self.get_user_by_username(username)
        
        if not user:
            raise VestaException("کاربر یافت نشد", 404)
        
        if not user.hashed_password:
            raise VestaException("رمز عبور تنظیم نشده است", 400)
        
        if not verify_password(password, user.hashed_password):
            raise VestaException("رمز عبور اشتباه است", 401)
        
        if not user.is_active:
            raise VestaException("حساب کاربری غیرفعال است", 403)
        
        # Update last login time
        user.last_login = datetime.now()
        self.db.commit()
        
        # Log activity
        self._log_activity(user.id, "login", "user", user.id, {
            "method": "password"
        })
        
        return user
    
    def request_otp(self, mobile: str) -> bool:
        """Request OTP for login"""
        # Format and validate mobile
        mobile = format_mobile(mobile)
        if not mobile:
            raise VestaException("شماره موبایل نامعتبر است", 400)
        
        # Generate OTP
        from app.core.security import generate_otp
        otp = generate_otp()
        
        # Save OTP
        success = self.otp_service.save_otp(mobile, otp)
        if not success:
            raise VestaException("خطا در ذخیره کد تأیید", 500)
        
        # Get or create user
        user = self.get_user_by_mobile(mobile)
        if not user:
            # Create a new user with minimal info
            try:
                user_in = UserCreate(
                    mobile=mobile,
                    first_name="کاربر",
                    last_name="جدید",
                    role=UserRole.AGENT
                )
                user = self.create_user(user_in)
            except Exception as e:
                raise VestaException(f"خطا در ایجاد کاربر: {str(e)}", 500)
        
        return True
    
    def verify_otp(self, mobile: str, otp: str) -> Optional[User]:
        """Verify OTP for login"""
        # Format mobile
        mobile = format_mobile(mobile)
        if not mobile:
            raise VestaException("شماره موبایل نامعتبر است", 400)
        
        # Verify OTP
        if not self.otp_service.verify_otp(mobile, otp):
            raise VestaException("کد تأیید اشتباه یا منقضی شده است", 401)
        
        # Get user
        user = self.get_user_by_mobile(mobile)
        if not user:
            raise VestaException("کاربر یافت نشد", 404)
        
        if not user.is_active:
            raise VestaException("حساب کاربری غیرفعال است", 403)
        
        # Update last login time
        user.last_login = datetime.now()
        self.db.commit()
        
        # Log activity
        self._log_activity(user.id, "login", "user", user.id, {
            "method": "otp"
        })
        
        return user
    
    def create_user(self, user_in: UserCreate) -> User:
        # Format and validate mobile
        mobile = format_mobile(user_in.mobile)
        if not mobile:
            raise VestaException("شماره موبایل نامعتبر است", 400)
        
        # Check if mobile already exists
        existing_user = self.get_user_by_mobile(mobile)
        if existing_user:
            raise VestaException("کاربری با این شماره موبایل وجود دارد", 400)
        
        # Generate a unique ID
        user_id = generate_id("USR")
        
        # Generate username from mobile if not provided
        username = mobile
        
        # Create user object
        user_data = user_in.dict(exclude={"password"})
        user_data["id"] = user_id
        user_data["username"] = username
        user_data["mobile"] = mobile
        
        # Hash password if provided
        if user_in.password:
            user_data["hashed_password"] = get_password_hash(user_in.password)
        
        # Create user
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        # If user role is AGENT, create agent record
        if user.role == UserRole.AGENT:
            agent_id = generate_id("AGT")
            agent = Agent(id=agent_id, user_id=user.id)
            self.db.add(agent)
            
            # Create credit record for agent
            credit_id = generate_id("CRD")
            credit = Credit(id=credit_id, agent_id=agent_id, balance=0)
            self.db.add(credit)
            
            self.db.commit()
        
        # Log activity
        self._log_activity(user.id, "create", "user", user.id, {
            "role": user.role.value
        })
        
        return user
    
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
