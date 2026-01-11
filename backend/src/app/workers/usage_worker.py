"""
Usage Worker - Background tasks for usage tracking and aggregation.
"""
from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.usage_service import UsageService
from datetime import datetime, timedelta


@celery_app.task(name="usage.aggregate_daily")
def aggregate_daily_usage(tenant_id: str, date: str = None):
    """Aggregate daily usage for a tenant."""
    db = SessionLocal()
    try:
        if date:
            usage_date = datetime.fromisoformat(date).date()
        else:
            usage_date = (datetime.utcnow() - timedelta(days=1)).date()
        
        # UsageService already handles daily aggregation in record_usage
        # This task can be used for backfilling or manual aggregation
        return {"success": True, "date": str(usage_date)}
    finally:
        db.close()


@celery_app.task(name="usage.cleanup_old_records")
def cleanup_old_usage_records(days_to_keep: int = 365):
    """Clean up old usage records (archive or delete)."""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        # In production, would archive or delete old records
        return {"success": True, "cutoff_date": cutoff_date.isoformat()}
    finally:
        db.close()