"""
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
    
    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved name conflict)
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata
    tags = Column(JSON, nullable=True)  # Tags for organization
    
    # Lineage (tracking)
    prompt_used = Column(Text, nullable=True)  # Prompt that generated this
    model_used = Column(String, nullable=True)  # Model that generated this
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="artifacts", lazy="select")
    # run = relationship("Run", back_populates="artifact")
    # social_posts = relationship("SocialPost", back_populates="artifact")