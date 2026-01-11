#!/usr/bin/env python3
"""Fix all model files with encoding issues"""
import os

files_to_fix = {
    'src/app/db/models/artifact.py': '''"""
Artifact model - represents business outputs (post, image, reel script, video).
Artifacts are immutable and versioned. Never overwrite content.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Enum, JSON, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class ArtifactType(str, enum.Enum):
    POST = "POST"
    IMAGE = "IMAGE"
    REEL = "REEL"
    VIDEO = "VIDEO"
    SHORT = "SHORT"
    SCRIPT = "SCRIPT"
    OTHER = "OTHER"


class ArtifactStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Run reference (which AI run created this)
    run_id = Column(String, ForeignKey("runs.id"), nullable=True, index=True)
    
    # Artifact metadata
    type = Column(Enum(ArtifactType), nullable=False, index=True)
    status = Column(Enum(ArtifactStatus), default=ArtifactStatus.DRAFT, nullable=False)
    version = Column(Integer, default=1, nullable=False)  # Version number
    parent_artifact_id = Column(String, ForeignKey("artifacts.id"), nullable=True)  # For versioning
    
    # Content
    title = Column(String, nullable=True)
    content = Column(Text, nullable=True)  # Text content (for posts, scripts)
    content_data = Column(JSON, nullable=True)  # Structured content (for images, videos)
    
    # Media references
    image_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional metadata
    tags = Column(JSON, nullable=True)  # Tags for organization
    
    # Lineage (tracking)
    prompt_used = Column(Text, nullable=True)  # Prompt that generated this
    model_used = Column(String, nullable=True)  # Model that generated this
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    # run = relationship("Run", back_populates="artifact")
    # social_posts = relationship("SocialPost", back_populates="artifact")
''',
    'src/app/db/models/prompt_version.py': '''"""
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
    metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)

    # Relationships
    # runs = relationship("Run", back_populates="prompt_version")
'''
}

for filepath, content in files_to_fix.items():
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed {filepath}")

print("All files fixed!")
