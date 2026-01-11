"""
Activity Timeline model - audit trail of user/tenant activities.
Tracks all significant actions for compliance and debugging.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class ActivityType(str, enum.Enum):
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_UPDATED = "PROJECT_UPDATED"
    CONVERSATION_CREATED = "CONVERSATION_CREATED"
    RUN_STARTED = "RUN_STARTED"
    RUN_COMPLETED = "RUN_COMPLETED"
    ARTIFACT_CREATED = "ARTIFACT_CREATED"
    ARTIFACT_PUBLISHED = "ARTIFACT_PUBLISHED"
    POST_PUBLISHED = "POST_PUBLISHED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    INVOICE_CREATED = "INVOICE_CREATED"
    OTHER = "OTHER"


class ActivityTimeline(Base):
    __tablename__ = "activity_timeline"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    
    # Activity details
    activity_type = Column(Enum(ActivityType), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Related entity
    entity_type = Column(String, nullable=True)  # e.g., "project", "conversation", "run"
    entity_id = Column(String, nullable=True, index=True)
    
    # Additional data
    extra_metadata = Column(JSON, nullable=True)  # Additional context
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="activity_timeline")

