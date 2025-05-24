pythonfrom typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_admin
from app.core.security import generate_id
from app.models.user import User, UserRole
from app.schemas.agent import AgentCreate, AgentResponse, AgentUpdate
from app.services.agent_service import AgentService

router = APIRouter()

@router.get("/", response_model=List[AgentResponse])
def get_agents(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Retrieve agents.
    """
    agent_service = AgentService(db)
    agents = agent_service.get_agents(skip=skip, limit=limit, search=search)
    return agents

@router.post("/", response_model=AgentResponse)
def create_agent(
    agent_in: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Create new agent.
    """
    agent_service = AgentService(db)
    agent = agent_service.create_agent(agent_in)
    return agent

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get agent by ID.
    """
    agent_service = AgentService(db)
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    # Only admins or the agent itself can see the agent details
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN] and agent.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_id: str,
    agent_in: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Update an agent.
    """
    agent_service = AgentService(db)
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    agent = agent_service.update_agent(agent_id, agent_in)
    return agent

@router.post("/{agent_id}/activate", response_model=AgentResponse)
def activate_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Activate an agent.
    """
    agent_service = AgentService(db)
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    agent = agent_service.activate_agent(agent_id)
    return agent

@router.post("/{agent_id}/deactivate", response_model=AgentResponse)
def deactivate_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Deactivate an agent.
    """
    agent_service = AgentService(db)
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    agent = agent_service.deactivate_agent(agent_id)
    return agent