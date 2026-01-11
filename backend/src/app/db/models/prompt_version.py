"""
Prompt Version model - versioned prompts for A/B testing and experimentation.
Never overwrite prompts, always create new versions.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True, index=True)  # Null = global prompt
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True, index=True)
    
    # Prompt identification
    prompt_name = Column(String, nullable=False, index=True)  # e.g., "post_generation_v1"
    version = Column(String, nullable=False)  # Semantic versioning: "1.0.0", "1.1.0"
    
    # Prompt content
    system_prompt = Column(Text, nullable=True)
    user_prompt_template = Column(Text, nullable=False)  # Template with variables
    variables = Column(JSON, nullable=True)  # Available variables in template
    
    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)  # Only one active per prompt_name
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Experimentation
    experiment_id = Column(String, nullable=True)  # For A/B testing
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)

    # Relationships
    # runs = relationship("Run", back_populates="prompt_version")