pythonfrom typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserBase(BaseModel):
    mobile: str
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.AGENT
    is_active: Optional[bool] = True
    phone: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    business_name: Optional[str] = None
    telegram_id: Optional[str] = None
    whatsapp: Optional[str] = None


class UserCreate(UserBase):
    password: Optional[str] = None


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserResponse(UserBase):
    id: str
    username: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True