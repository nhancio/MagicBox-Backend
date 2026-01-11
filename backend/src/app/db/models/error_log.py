"""
Error Log model - tracks application errors for debugging and monitoring.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Enum, JSON, Integer, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class ErrorSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    
    # Error details
    severity = Column(Enum(ErrorSeverity), default=ErrorSeverity.MEDIUM, nullable=False, index=True)
    error_type = Column(String, nullable=False)  # Exception class name
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    
    # Context
    endpoint = Column(String, nullable=True)  # API endpoint
    method = Column(String, nullable=True)  # HTTP method
    request_id = Column(String, nullable=True)  # Request ID for tracing
    
    # Related entity
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    
    # Additional data
    extra_metadata = Column(JSON, nullable=True)
    
    # Resolution
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="error_logs")

