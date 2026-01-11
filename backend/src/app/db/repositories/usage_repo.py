"""
Usage Repository - Data access layer for Usage operations.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.models.llm_usage import LLMUsageRecord
from app.db.models.tenant_usage_daily import TenantUsageDaily


class UsageRepository:
    """Repository for Usage operations."""
    
    @staticmethod
    def get_by_tenant(
        db: Session,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LLMUsageRecord]:
        """Get usage records by tenant."""
        query = db.query(LLMUsageRecord).filter(LLMUsageRecord.tenant_id == tenant_id)
        
        if start_date:
            query = query.filter(LLMUsageRecord.created_at >= start_date)
        if end_date:
            query = query.filter(LLMUsageRecord.created_at <= end_date)
        
        return query.order_by(LLMUsageRecord.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_daily_usage(
        db: Session,
        tenant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TenantUsageDaily]:
        """Get daily usage aggregation."""
        query = db.query(TenantUsageDaily).filter(TenantUsageDaily.tenant_id == tenant_id)
        
        if start_date:
            query = query.filter(TenantUsageDaily.usage_date >= start_date.date())
        if end_date:
            query = query.filter(TenantUsageDaily.usage_date <= end_date.date())
        
        return query.order_by(TenantUsageDaily.usage_date.desc()).all()
