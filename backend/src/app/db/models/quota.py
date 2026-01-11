"""
Quota model - tracks usage quotas per tenant/plan.
Enforces limits before allowing operations.
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Float, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid


class Quota(Base):
    __tablename__ = "quotas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    plan_id = Column(String, ForeignKey("plans.id"), nullable=False, index=True)
    
    # Current usage (denormalized for quick access)
    current_usage = Column(JSON, nullable=False)  # e.g., {"runs_this_month": 150, "tokens_this_month": 50000}
    
    # Limits from plan (denormalized)
    limits = Column(JSON, nullable=False)  # e.g., {"runs_per_month": 1000, "tokens_per_month": 1000000}
    
    # Billing period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="quotas")

