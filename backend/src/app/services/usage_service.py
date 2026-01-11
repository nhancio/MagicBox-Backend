"""
Usage Service - Tracks LLM usage and costs for billing and analytics.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.db.models.llm_usage import LLMUsageRecord, UsageType
from app.db.models.tenant_usage_daily import TenantUsageDaily
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID
import uuid


class UsageService:
    """Service for tracking LLM usage."""
    
    @staticmethod
    def record_usage(
        db: Session,
        usage_type: UsageType,
        provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Optional[float] = None,
        run_id: Optional[str] = None,
        project_id: Optional[str] = None,
        model_version: Optional[str] = None,
        cost_per_1k_input: Optional[float] = None,
        cost_per_1k_output: Optional[float] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMUsageRecord:
        """Record LLM usage."""
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id:
            raise ValueError("Tenant ID not found in context")
        
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost if not provided
        if cost_usd is None:
            if cost_per_1k_input and cost_per_1k_output:
                cost_usd = (
                    (input_tokens / 1000) * cost_per_1k_input +
                    (output_tokens / 1000) * cost_per_1k_output
                )
        
        usage_date = datetime.utcnow().date()
        
        record = LLMUsageRecord(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            project_id=project_id,
            run_id=run_id,
            usage_type=usage_type,
            provider=provider,
            model_name=model_name,
            model_version=model_version,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            cost_per_1k_input=cost_per_1k_input,
            cost_per_1k_output=cost_per_1k_output,
            extra_metadata=extra_metadata,
            usage_date=usage_date,
        )
        
        db.add(record)
        
        # Update daily usage aggregation
        UsageService._update_daily_usage(db, tenant_id, usage_date, total_tokens, cost_usd)
        
        db.commit()
        db.refresh(record)
        return record
    
    @staticmethod
    def _update_daily_usage(
        db: Session,
        tenant_id: str,
        usage_date: datetime.date,
        tokens: int,
        cost: Optional[float],
    ):
        """Update daily usage aggregation."""
        daily = db.query(TenantUsageDaily).filter(
            TenantUsageDaily.tenant_id == tenant_id,
            TenantUsageDaily.usage_date == usage_date,
        ).first()
        
        if not daily:
            daily = TenantUsageDaily(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                usage_date=usage_date,
                total_tokens=0,
                total_cost_usd=0.0,
            )
            db.add(daily)
        
        daily.total_tokens += tokens
        if cost:
            daily.total_cost_usd = (daily.total_cost_usd or 0.0) + cost
    
    @staticmethod
    def get_usage_stats(
        db: Session,
        tenant_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get usage statistics."""
        if not tenant_id:
            tenant_id = get_context(CTX_TENANT_ID)
        
        query = db.query(LLMUsageRecord).filter(LLMUsageRecord.tenant_id == tenant_id)
        
        if start_date:
            query = query.filter(LLMUsageRecord.created_at >= start_date)
        if end_date:
            query = query.filter(LLMUsageRecord.created_at <= end_date)
        
        records = query.all()
        
        total_tokens = sum(r.total_tokens for r in records)
        total_cost = sum(r.cost_usd or 0.0 for r in records)
        
        # Group by usage type
        by_type = {}
        for record in records:
            usage_type = record.usage_type.value
            if usage_type not in by_type:
                by_type[usage_type] = {"count": 0, "tokens": 0, "cost": 0.0}
            by_type[usage_type]["count"] += 1
            by_type[usage_type]["tokens"] += record.total_tokens
            by_type[usage_type]["cost"] += record.cost_usd or 0.0
        
        return {
            "total_records": len(records),
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "by_type": by_type,
        }
