pythonfrom typing import Optional, List
from pydantic import BaseModel


class AgentGroupBase(BaseModel):
    name: str
    description: Optional[str] = None


class AgentGroupCreate(AgentGroupBase):
    pass


class AgentGroupUpdate(AgentGroupBase):
    pass


class AgentGroupResponse(AgentGroupBase):
    id: str
    agent_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True