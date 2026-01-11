"""
Social Post model - tracks posts published to social media platforms.
Links to artifacts and tracks status/metrics.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Enum, JSON, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class PostStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SocialPost(Base):
    __tablename__ = "social_posts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)
    artifact_id = Column(String, ForeignKey("artifacts.id"), nullable=True, index=True)
    social_account_id = Column(String, ForeignKey("social_accounts.id"), nullable=False, index=True)
    
    # Post content
    content = Column(Text, nullable=False)
    media_urls = Column(JSON, nullable=True)  # Array of media URLs
    
    # Scheduling
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT, nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=True, index=True)
    published_at = Column(DateTime, nullable=True)
    
    # External references
    external_post_id = Column(String, nullable=True)  # ID from social platform
    external_url = Column(String, nullable=True)  # URL to published post
    
    # Metrics (updated after publishing)
    likes_count = Column(Integer, default=0, nullable=False)
    comments_count = Column(Integer, default=0, nullable=False)
    shares_count = Column(Integer, default=0, nullable=False)
    views_count = Column(Integer, default=0, nullable=False)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="social_posts")

