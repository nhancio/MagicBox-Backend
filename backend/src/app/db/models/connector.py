"""
Connector model - stores connector configurations for different platforms.
Each connector type has its own configuration schema stored as JSON.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class ConnectorType(str, enum.Enum):
    """Supported connector types."""
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    TWITTER = "TWITTER"
    LINKEDIN = "LINKEDIN"
    YOUTUBE = "YOUTUBE"
    TIKTOK = "TIKTOK"
    OTHER = "OTHER"


class ConnectorStatus(str, enum.Enum):
    """Connector status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    PENDING_SETUP = "PENDING_SETUP"


class Connector(Base):
    """Connector configuration model."""
    __tablename__ = "connectors"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Connector identification
    name = Column(String, nullable=False)  # User-friendly name
    connector_type = Column(Enum(ConnectorType), nullable=False, index=True)
    status = Column(Enum(ConnectorStatus), default=ConnectorStatus.PENDING_SETUP, nullable=False, index=True)
    
    # Configuration (platform-specific, stored as JSON)
    # Each connector type has different required fields
    config = Column(JSON, nullable=False)  # Platform-specific configuration
    
    # Status and metadata
    last_verified_at = Column(DateTime, nullable=True)  # Last time credentials were verified
    last_error = Column(Text, nullable=True)  # Last error message if status is ERROR
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="connectors")
