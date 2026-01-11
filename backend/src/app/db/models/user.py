"""
User model - user accounts with multi-tenant support.
Enhanced with relationships and proper structure.
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)

    # auth
    auth_provider = Column(String, nullable=False)  # "local" | "google"
    provider_id = Column(String, nullable=True)     # google sub
    password_hash = Column(String, nullable=True)  # only for local auth

    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    role = Column(String, ForeignKey("roles.name"), nullable=False)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    role_rel = relationship("Role", back_populates="users")
