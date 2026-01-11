"""
Social Account model - stores connected social media accounts.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class SocialPlatform(str, enum.Enum):
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    TWITTER = "TWITTER"
    LINKEDIN = "LINKEDIN"
    TIKTOK = "TIKTOK"
    YOUTUBE = "YOUTUBE"
    OTHER = "OTHER"


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Platform details
    platform = Column(Enum(SocialPlatform), nullable=False, index=True)
    account_name = Column(String, nullable=False)  # Display name
    account_id = Column(String, nullable=True)  # Platform-specific account ID
    
    # OAuth tokens (encrypted)
    access_token = Column(Text, nullable=True)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    token_expires_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_connected = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)  # Platform-specific metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="social_accounts")

