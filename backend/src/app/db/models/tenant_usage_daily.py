"""
Tenant Usage Daily model - aggregated daily usage for reporting and analytics.
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Float, JSON
from app.db.base import Base
from datetime import datetime
import uuid


class TenantUsageDaily(Base):
    __tablename__ = "tenant_usage_daily"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Date (YYYY-MM-DD)
    usage_date = Column(DateTime, nullable=False, index=True)
    
    # Aggregated metrics
    total_runs = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    total_cost_usd = Column(Float, default=0.0, nullable=False)
    
    # Breakdown by type
    completion_tokens = Column(Integer, default=0, nullable=False)
    embedding_tokens = Column(Integer, default=0, nullable=False)
    image_generations = Column(Integer, default=0, nullable=False)
    video_generations = Column(Integer, default=0, nullable=False)
    
    # Detailed breakdown (JSON)
    breakdown = Column(JSON, nullable=True)  # Detailed breakdown by model, etc.
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Unique constraint on tenant_id + usage_date
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

