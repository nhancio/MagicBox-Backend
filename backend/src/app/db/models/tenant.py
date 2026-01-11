"""
Tenant model - multi-tenant isolation.
Enhanced with metadata and relationships.
"""
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    user_tenant_roles = relationship("UserTenantRole", back_populates="tenant")
    projects = relationship("Project", back_populates="tenant")
    conversations = relationship("Conversation", back_populates="tenant")
    agents = relationship("Agent", back_populates="tenant")
    runs = relationship("Run", back_populates="tenant")
    artifacts = relationship("Artifact", back_populates="tenant")
    embeddings = relationship("Embedding", back_populates="tenant")
    credit_accounts = relationship("CreditAccount", back_populates="tenant")
    invoices = relationship("Invoice", back_populates="tenant")
    quotas = relationship("Quota", back_populates="tenant")
    social_accounts = relationship("SocialAccount", back_populates="tenant")
    social_posts = relationship("SocialPost", back_populates="tenant")
    oauth_states = relationship("OAuthState", back_populates="tenant")
    activity_timeline = relationship("ActivityTimeline", back_populates="tenant")
    events = relationship("Event", back_populates="tenant")
    error_logs = relationship("ErrorLog", back_populates="tenant")