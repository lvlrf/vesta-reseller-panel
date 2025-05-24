pythonfrom sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

class Credit(Base):
    __tablename__ = "credits"

    id = Column(String, primary_key=True, index=True)  # مثال: CRD-12345
    agent_id = Column(String, ForeignKey("agents.id"))
    balance = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    agent = relationship("Agent", back_populates="credits")
    transactions = relationship("Transaction", back_populates="credit")