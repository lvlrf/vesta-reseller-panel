pythonfrom typing import Optional, Dict, Any
from datetime import datetime
import re

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import get_password_hash, verify_password, generate_id
from app.core.utils import validate_mobile, format_mobile
from app.models.user import User, UserRole
from app.models.agent import Agent
from app.models.credit import Credit
from app.models.activity_log import ActivityLog
from app.schemas.user import UserCreate, UserUpdate


class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
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
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Update last login time
        user.last_login = datetime.now()
        self.db.commit()
        
        # Log activity
        self._log_activity(user.id, "login", "user", user.id, {
            "method": "password"
        })
        
        return user
    
    def create_user(self, user_in: UserCreate) -> User:
        # Format and validate mobile
        mobile = format_mobile(user_in.mobile)
        if not mobile:
            raise ValueError("Invalid mobile number")
        
        # Check if mobile already exists
        existing_user = self.get_user_by_mobile(mobile)
        if existing_user:
            raise ValueError("User with this mobile already exists")
        
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
            "role": user.role
        })
        
        return user
    
    def update_user(self, user_id: str, user_in: UserUpdate) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Format and validate mobile if changed
        if user_in.mobile and user_in.mobile != user.mobile:
            mobile = format_mobile(user_in.mobile)
            if not mobile:
                raise ValueError("Invalid mobile number")
            
            # Check if mobile already exists
            existing_user = self.get_user_by_mobile(mobile)
            if existing_user and existing_user.id != user_id:
                raise ValueError("User with this mobile already exists")
            
            user_in.mobile = mobile
        
        # Update user fields
        update_data = user_in.dict(exclude_unset=True)
        
        # Hash new password if provided
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        # Log activity
        self._log_activity(user.id, "update", "user", user.id, {})
        
        return user
    
    def save_otp(self, mobile: str, otp: str) -> bool:
        """
        Save OTP for a user. In a real implementation, this would use Redis or similar.
        For now, we'll just use a temporary placeholder.
        """
        # Format mobile
        mobile = format_mobile(mobile)
        if not mobile:
            return False
        
        # Get or create user
        user = self.get_user_by_mobile(mobile)
        if not user:
            # Create a new user with minimal info
            try:
                user_in = UserCreate(
                    mobile=mobile,
                    first_name="New",
                    last_name="User",
                    role=UserRole.AGENT
                )
                user = self.create_user(user_in)
            except Exception as e:
                print(f"Error creating user: {e}")
                return False
        
        # In a real implementation, store OTP in Redis with expiry
        # For now, we'll just use a placeholder (this is not secure for production!)
        # Use a secure database or Redis in production
        user.hashed_password = get_password_hash(otp)
        self.db.commit()
        
        return True
    
    def verify_otp(self, mobile: str, otp: str) -> Optional[User]:
        """
        Verify OTP for a user.
        """
        # Format mobile
        mobile = format_mobile(mobile)
        if not mobile:
            return None
        
        # Get user
        user = self.get_user_by_mobile(mobile)
        if not user:
            return None
        
        # Verify OTP (in a real implementation, this would check Redis)
        # For now, we'll just check against the user's password
        if not verify_password(otp, user.hashed_password):
            return None
        
        # Update last login time
        user.last_login = datetime.now()
        self.db.commit()
        
        # Log activity
        self._log_activity(user.id, "login", "user", user.id, {
            "method": "otp"
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