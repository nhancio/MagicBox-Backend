"""
Role model - defines user roles with permissions and metadata.
Roles are used for RBAC (Role-Based Access Control).
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime


class Role(Base):
    __tablename__ = "roles"

    name = Column(String, primary_key=True)  # e.g., "OWNER", "ADMIN", "EDITOR", "VIEWER"
    description = Column(Text, nullable=True)  # Human-readable description
    
    # Permissions (stored as JSON for flexibility)
    permissions = Column(JSON, nullable=True)  # List of permission strings or permission object
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_role = Column(Boolean, default=False, nullable=False)  # System roles cannot be deleted
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="role_rel")
    user_tenant_roles = relationship("UserTenantRole", back_populates="role_rel")
