pythonfrom sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.agent import agent_group_association

class AgentGroup(Base):
    __tablename__ = "agent_groups"

    id = Column(String, primary_key=True, index=True)  # مثال: AGG-12345
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    agents = relationship("Agent", secondary=agent_group_association, back_populates="groups")