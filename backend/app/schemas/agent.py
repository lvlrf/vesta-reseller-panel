pythonfrom typing import Optional, List
from pydantic import BaseModel

from app.schemas.user import UserResponse


class AgentBase(BaseModel):
    user_id: str
    group_ids: Optional[List[str]] = None


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    group_ids: Optional[List[str]] = None


class AgentResponse(BaseModel):
    id: str
    user: UserResponse
    group_names: List[str] = []
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True