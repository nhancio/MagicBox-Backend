"""
Project-Agent relationship model - links agents to projects.
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class ProjectAgent(Base):
    """Junction table for project-agent relationships."""
    __tablename__ = "project_agents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Configuration override for this project-agent combination
    config_override = Column(JSON, nullable=True)  # Project-specific agent config
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="agents")
    agent = relationship("Agent", back_populates="projects")
