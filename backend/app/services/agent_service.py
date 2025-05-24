pythonfrom typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import generate_id
from app.models.user import User, UserRole
from app.models.agent import Agent
from app.models.agent_group import AgentGroup
from app.models.credit import Credit
from app.schemas.agent import AgentCreate, AgentUpdate
from app.schemas.agent_group import AgentGroupCreate, AgentGroupUpdate


class AgentService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_agents(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[Agent]:
        """Get all agents with optional search"""
        query = self.db.query(Agent)
        
        if search:
            # Search in user fields
            query = query.join(User).filter(
                (User.first_name.ilike(f"%{search}%")) |
                (User.last_name.ilike(f"%{search}%")) |
                (User.mobile.ilike(f"%{search}%")) |
                (User.email.ilike(f"%{search}%")) |
                (User.business_name.ilike(f"%{search}%"))
            )
        
        return query.offset(skip).limit(limit).all()
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID"""
        return self.db.query(Agent).filter(Agent.id == agent_id).first()
    
    def get_agent_by_user_id(self, user_id: str) -> Optional[Agent]:
        """Get agent by user ID"""
        return self.db.query(Agent).filter(Agent.user_id == user_id).first()
    
    def create_agent(self, agent_in: AgentCreate) -> Agent:
        """Create a new agent"""
        # Check if user exists
        user = self.db.query(User).filter(User.id == agent_in.user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Check if user already has an agent record
        existing_agent = self.get_agent_by_user_id(agent_in.user_id)
        if existing_agent:
            raise ValueError("User already has an agent record")
        
        # Create agent
        agent_id = generate_id("AGT")
        agent = Agent(id=agent_id, user_id=agent_in.user_id)
        self.db.add(agent)
        
        # Create credit record for agent
        credit_id = generate_id("CRD")
        credit = Credit(id=credit_id, agent_id=agent_id, balance=0)
        self.db.add(credit)
        
        # Set user role to AGENT if not already
        if user.role != UserRole.AGENT:
            user.role = UserRole.AGENT
        
        # Add to groups if specified
        if agent_in.group_ids:
            for group_id in agent_in.group_ids:
                group = self.get_agent_group(group_id)
                if group:
                    agent.groups.append(group)
        
        self.db.commit()
        self.db.refresh(agent)
        
        return agent
    
    def update_agent(self, agent_id: str, agent_in: AgentUpdate) -> Optional[Agent]:
        """Update an agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        # Update groups if specified
        if agent_in.group_ids is not None:
            # Clear existing groups
            agent.groups = []
            
            # Add to new groups
            for group_id in agent_in.group_ids:
                group = self.get_agent_group(group_id)
                if group:
                    agent.groups.append(group)
        
        self.db.commit()
        self.db.refresh(agent)
        
        return agent
    
    def activate_agent(self, agent_id: str) -> Optional[Agent]:
        """Activate an agent by activating their user account"""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        agent.user.is_active = True
        self.db.commit()
        self.db.refresh(agent)
        
        return agent
    
    def deactivate_agent(self, agent_id: str) -> Optional[Agent]:
        """Deactivate an agent by deactivating their user account"""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        
        agent.user.is_active = False
        self.db.commit()
        self.db.refresh(agent)
        
        return agent
    
    # Agent Group methods
    def get_agent_groups(self, skip: int = 0, limit: int = 100) -> List[AgentGroup]:
        """Get all agent groups"""
        return self.db.query(AgentGroup).offset(skip).limit(limit).all()
    
    def get_agent_group(self, group_id: str) -> Optional[AgentGroup]:
        """Get agent group by ID"""
        return self.db.query(AgentGroup).filter(AgentGroup.id == group_id).first()
    
    def create_agent_group(self, group_in: AgentGroupCreate) -> AgentGroup:
        """Create a new agent group"""
        group_id = generate_id("AGG")
        group = AgentGroup(
            id=group_id,
            name=group_in.name,
            description=group_in.description
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        
        return group
    
    def update_agent_group(self, group_id: str, group_in: AgentGroupUpdate) -> Optional[AgentGroup]:
        """Update an agent group"""
        group = self.get_agent_group(group_id)
        if not group:
            return None
        
        group.name = group_in.name
        group.description = group_in.description
        
        self.db.commit()
        self.db.refresh(group)
        
        return group
    
    def add_agent_to_group(self, agent_id: str, group_id: str) -> bool:
        """Add an agent to a group"""
        agent = self.get_agent(agent_id)
        group = self.get_agent_group(group_id)
        
        if not agent or not group:
            return False
        
        # Check if agent already in group
        if group in agent.groups:
            return False
        
        agent.groups.append(group)
        self.db.commit()
        
        return True
    
    def remove_agent_from_group(self, agent_id: str, group_id: str) -> bool:
        """Remove an agent from a group"""
        agent = self.get_agent(agent_id)
        group = self.get_agent_group(group_id)
        
        if not agent or not group:
            return False
        
        # Check if agent in group
        if group not in agent.groups:
            return False
        
        agent.groups.remove(group)
        self.db.commit()
        
        return True