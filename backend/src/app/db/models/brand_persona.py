"""
Brand Persona model - stores brand personality and guidelines for AI generation.
Attached to projects to guide content generation.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class BrandPersona(Base):
    __tablename__ = "brand_personas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    name = Column(String, nullable=False)  # e.g., "Professional", "Casual", "Creative"
    description = Column(Text, nullable=True)
    
    # Brand attributes stored as JSON for flexibility
    tone = Column(String, nullable=True)  # e.g., "friendly", "professional", "witty"
    style = Column(Text, nullable=True)  # Writing style guidelines
    keywords = Column(JSON, nullable=True)  # Preferred keywords/phrases
    avoid_keywords = Column(JSON, nullable=True)  # Keywords to avoid
    examples = Column(JSON, nullable=True)  # Example content
    
    # Metadata
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)

