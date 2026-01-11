"""
Agent model - represents a reusable AI worker with role + tools.
Agents are registered in the system and can be invoked for runs.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True, index=True)  # Null = global agent
    
    name = Column(String, nullable=False, unique=True)  # e.g., "post_agent", "image_agent"
    description = Column(Text, nullable=True)
    role = Column(String, nullable=False)  # Agent's role/purpose
    
    # Agent configuration
    default_model = Column(String, nullable=True)  # Default LLM model to use
    tools = Column(JSON, nullable=True)  # List of available tools
    system_prompt = Column(Text, nullable=True)  # System prompt template
    
    # Versioning
    version = Column(String, default="1.0.0", nullable=False)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="agents", lazy="select")

