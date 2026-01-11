
"""
Project model - represents a brand/workspace within a tenant.
Projects can have brand personas attached.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Brand persona settings
    brand_voice = Column(Text, nullable=True)  # Brand voice description
    target_audience = Column(Text, nullable=True)
    brand_guidelines = Column(Text, nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="projects", lazy="select")
    agents = relationship("ProjectAgent", back_populates="project", cascade="all, delete-orphan")
    # conversations = relationship("Conversation", back_populates="project")
    # artifacts = relationship("Artifact", back_populates="project")