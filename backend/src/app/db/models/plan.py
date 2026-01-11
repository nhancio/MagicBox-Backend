"""
Plan model - subscription plans with quotas and limits.
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, JSON
from app.db.base import Base
from datetime import datetime
import uuid


class Plan(Base):
    __tablename__ = "plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    name = Column(String, nullable=False, unique=True)  # e.g., "Free", "Pro", "Enterprise"
    description = Column(Text, nullable=True)
    
    # Pricing
    price_usd_per_month = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Quotas (stored as JSON for flexibility)
    quotas = Column(JSON, nullable=False)  # e.g., {"runs_per_month": 1000, "tokens_per_month": 1000000}
    
    # Features
    features = Column(JSON, nullable=True)  # List of enabled features
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

