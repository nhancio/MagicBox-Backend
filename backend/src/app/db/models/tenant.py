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
    
    # Relationships (commented out to avoid circular imports - enable after models are loaded)
    # users = relationship("User", back_populates="tenant")