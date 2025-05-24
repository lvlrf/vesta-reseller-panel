pythonfrom sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

# Association table for many-to-many relationship between Agent and AgentGroup
agent_group_association = Table(
    'agent_group_association',
    Base.metadata,
    Column('agent_id', String, ForeignKey('agents.id')),
    Column('group_id', String, ForeignKey('agent_groups.id'))
)

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True)  # مثال: AGT-12345
    user_id = Column(String, ForeignKey("users.id"), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="agent")
    groups = relationship("AgentGroup", secondary=agent_group_association, back_populates="agents")
    credits = relationship("Credit", back_populates="agent")
    created_subscriptions = relationship("Subscription", back_populates="agent")