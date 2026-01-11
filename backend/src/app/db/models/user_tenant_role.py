"""
User-Tenant-Role junction table for multi-tenant RBAC.
Supports users having different roles in different tenants.
"""
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class UserTenantRole(Base):
    __tablename__ = "user_tenant_roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    role = Column(String, ForeignKey("roles.name"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="user_tenant_roles")
    role_rel = relationship("Role", back_populates="user_tenant_roles")

