pythonfrom typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_admin
from app.models.user import User, UserRole
from app.schemas.agent_group import AgentGroupCreate, AgentGroupResponse, AgentGroupUpdate
from app.services.agent_service import AgentService

router = APIRouter()

@router.get("/", response_model=List[AgentGroupResponse])
def get_agent_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Retrieve agent groups.
    """
    agent_service = AgentService(db)
    groups = agent_service.get_agent_groups(skip=skip, limit=limit)
    return groups

@router.post("/", response_model=AgentGroupResponse)
def create_agent_group(
    group_in: AgentGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Create new agent group.
    """
    agent_service = AgentService(db)
    group = agent_service.create_agent_group(group_in)
    return group

@router.get("/{group_id}", response_model=AgentGroupResponse)
def get_agent_group(
    group_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Get agent group by ID.
    """
    agent_service = AgentService(db)
    group = agent_service.get_agent_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent group not found",
        )
    return group

@router.put("/{group_id}", response_model=AgentGroupResponse)
def update_agent_group(
    group_id: str,
    group_in: AgentGroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Update an agent group.
    """
    agent_service = AgentService(db)
    group = agent_service.get_agent_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent group not found",
        )
    
    group = agent_service.update_agent_group(group_id, group_in)
    return group

@router.post("/{group_id}/add-agent/{agent_id}")
def add_agent_to_group(
    group_id: str,
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Add an agent to a group.
    """
    agent_service = AgentService(db)
    group = agent_service.get_agent_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent group not found",
        )
    
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    success = agent_service.add_agent_to_group(agent_id, group_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent already in group",
        )
    
    return {"message": "Agent added to group successfully"}

@router.post("/{group_id}/remove-agent/{agent_id}")
def remove_agent_from_group(
    group_id: str,
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Remove an agent from a group.
    """
    agent_service = AgentService(db)
    group = agent_service.get_agent_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent group not found",
        )
    
    agent = agent_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    
    success = agent_service.remove_agent_from_group(agent_id, group_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Agent not in group",
        )
    
    return {"message": "Agent removed from group successfully"}