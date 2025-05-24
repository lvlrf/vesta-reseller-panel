pythonfrom typing import Optional
from datetime import datetime
from pydantic import BaseModel


class SettingBase(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    category: str = "general"


class SettingCreate(SettingBase):
    pass


class SettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None
    category: Optional[str] = None


class SettingResponse(SettingBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True