"""
Social Worker - Background tasks for social media operations.
"""
from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.scheduling_service import SchedulingService
from datetime import datetime


@celery_app.task(name="social.publish_post")
def publish_post_task(post_id: str):
    """Publish a scheduled post."""
    db = SessionLocal()
    try:
        from app.db.models.social_post import SocialPost
        
        post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
        if not post:
            return {"success": False, "error": "Post not found"}
        
        # Use SchedulingService to publish
        SchedulingService.publish_now(db, post)
        return {"success": True, "post_id": post_id}
    finally:
        db.close()


@celery_app.task(name="social.sync_account_metrics")
def sync_account_metrics_task(account_id: str):
    """Sync metrics for a social account."""
    db = SessionLocal()
    try:
        # In production, would fetch metrics from social platform APIs
        return {"success": True, "account_id": account_id}
    finally:
        db.close()