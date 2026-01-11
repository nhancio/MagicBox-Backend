"""
Event model - system events for event-driven architecture.
Workers consume events for async processing.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Enum, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class EventType(str, enum.Enum):
    RUN_COMPLETED = "RUN_COMPLETED"
    ARTIFACT_CREATED = "ARTIFACT_CREATED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    POST_PUBLISHED = "POST_PUBLISHED"
    INVOICE_DUE = "INVOICE_DUE"
    USER_CREATED = "USER_CREATED"
    GDPR_DELETE_REQUESTED = "GDPR_DELETE_REQUESTED"
    OTHER = "OTHER"


class EventStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True, index=True)
    
    # Event details
    event_type = Column(Enum(EventType), nullable=False, index=True)
    status = Column(Enum(EventStatus), default=EventStatus.PENDING, nullable=False, index=True)
    
    # Payload
    payload = Column(JSON, nullable=False)  # Event data
    
    # Processing
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="events")

