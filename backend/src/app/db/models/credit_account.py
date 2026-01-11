"""
Credit Account model - tracks credit balances for tenants.
Used for prepaid billing models.
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class CreditAccount(Base):
    __tablename__ = "credit_accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    
    # Balance
    balance = Column(Float, default=0.0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="credit_accounts")

