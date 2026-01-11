"""
Scheduling Service - Manages scheduled posts and notifications.
Handles recurring schedules and one-time schedules.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import uuid

from app.db.models.social_post import SocialPost, PostStatus
from app.db.models.user import User
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID
from app.services.social_service import SocialService
from app.integrations.whatsapp import WhatsAppIntegration


class SchedulingService:
    """Service for scheduling posts and managing notifications."""
    
    @staticmethod
    def schedule_post(
        db: Session,
        account_id: str,
        content: str,
        scheduled_at: datetime,
        media_urls: Optional[List[str]] = None,
        notify_before_hours: int = 1,
        user_phone: Optional[str] = None,
        is_recurring: bool = False,
        recurrence_pattern: Optional[str] = None,  # "daily", "weekly", "monthly"
        recurrence_end_date: Optional[datetime] = None,
    ) -> SocialPost:
        """
        Schedule a post for future publishing.
        
        Args:
            db: Database session
            account_id: Social account ID
            content: Post content
            scheduled_at: When to publish
            media_urls: Optional media URLs
            notify_before_hours: Hours before post to send notification (default: 1)
            user_phone: User's WhatsApp number for notifications
            is_recurring: Whether this is a recurring post
            recurrence_pattern: Recurrence pattern (daily, weekly, monthly)
            recurrence_end_date: When to stop recurring
        
        Returns:
            Created SocialPost
        """
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id or not user_id:
            raise ValueError("Tenant ID and User ID must be in request context")
        
        # Validate scheduled time is in the future
        if scheduled_at <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")
        
        # Create post with SCHEDULED status
        post = SocialPost(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            social_account_id=account_id,
            content=content,
            media_urls=media_urls or [],
            status=PostStatus.SCHEDULED,
            scheduled_at=scheduled_at,
            created_by=user_id,
            extra_metadata={
                "notify_before_hours": notify_before_hours,
                "user_phone": user_phone,
                "is_recurring": is_recurring,
                "recurrence_pattern": recurrence_pattern,
                "recurrence_end_date": recurrence_end_date.isoformat() if recurrence_end_date else None,
            }
        )
        
        db.add(post)
        db.commit()
        db.refresh(post)
        
        # Schedule notification task (1 hour before post)
        notification_time = scheduled_at - timedelta(hours=notify_before_hours)
        if notification_time > datetime.utcnow() and user_phone:
            try:
                from app.tasks.notification_tasks import send_pre_post_notification
                send_pre_post_notification.apply_async(
                    args=[post.id, user_phone],
                    eta=notification_time
                )
            except Exception as e:
                # Log error but don't fail scheduling
                print(f"Failed to schedule notification (Celery may not be running): {e}")
        
        # Schedule post publishing task
        try:
            from app.tasks.publishing_tasks import publish_scheduled_post
            publish_scheduled_post.apply_async(
                args=[post.id],
                eta=scheduled_at
            )
        except Exception as e:
            # If Celery not available, mark for manual processing
            print(f"Failed to schedule post (Celery may not be running): {e}")
            # In production, you might want to use a database-based scheduler as fallback
        
        return post
    
    @staticmethod
    def create_recurring_schedule(
        db: Session,
        account_id: str,
        content: str,
        start_date: datetime,
        time_of_day: str,  # "09:00" format
        recurrence_pattern: str,  # "daily", "weekly", "monthly"
        recurrence_end_date: Optional[datetime] = None,
        notify_before_hours: int = 1,
        user_phone: Optional[str] = None,
    ) -> List[SocialPost]:
        """
        Create a recurring schedule for posts.
        
        Args:
            db: Database session
            account_id: Social account ID
            content: Post content
            start_date: When to start the schedule
            time_of_day: Time of day to post (HH:MM format)
            recurrence_pattern: "daily", "weekly", or "monthly"
            recurrence_end_date: When to stop (optional)
            notify_before_hours: Hours before to notify
            user_phone: User's WhatsApp number
        
        Returns:
            List of created SocialPost records
        """
        posts = []
        current_date = start_date
        
        # Parse time of day
        hour, minute = map(int, time_of_day.split(':'))
        
        while True:
            # Create scheduled datetime
            scheduled_at = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Check if we've passed the end date
            if recurrence_end_date and scheduled_at > recurrence_end_date:
                break
            
            # Only schedule future posts
            if scheduled_at > datetime.utcnow():
                post = SchedulingService.schedule_post(
                    db=db,
                    account_id=account_id,
                    content=content,
                    scheduled_at=scheduled_at,
                    notify_before_hours=notify_before_hours,
                    user_phone=user_phone,
                    is_recurring=True,
                    recurrence_pattern=recurrence_pattern,
                    recurrence_end_date=recurrence_end_date,
                )
                posts.append(post)
            
            # Calculate next occurrence
            if recurrence_pattern == "daily":
                current_date += timedelta(days=1)
            elif recurrence_pattern == "weekly":
                current_date += timedelta(weeks=1)
            elif recurrence_pattern == "monthly":
                # Add approximately 30 days (simplified)
                current_date += timedelta(days=30)
            else:
                break
            
            # Limit to 365 days ahead
            if current_date > datetime.utcnow() + timedelta(days=365):
                break
        
        return posts
    
    @staticmethod
    def cancel_scheduled_post(db: Session, post_id: str) -> bool:
        """Cancel a scheduled post."""
        tenant_id = get_context(CTX_TENANT_ID)
        if not tenant_id:
            raise ValueError("Tenant ID not found in request context")
        
        post = db.query(SocialPost).filter(
            SocialPost.id == post_id,
            SocialPost.tenant_id == tenant_id,
            SocialPost.status == PostStatus.SCHEDULED
        ).first()
        
        if not post:
            return False
        
        post.status = PostStatus.CANCELLED
        db.commit()
        
        # Revoke Celery tasks if possible
        # (This would require storing task IDs, simplified for now)
        
        return True
    
    @staticmethod
    def list_scheduled_posts(
        db: Session,
        account_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SocialPost]:
        """List scheduled posts."""
        tenant_id = get_context(CTX_TENANT_ID)
        if not tenant_id:
            raise ValueError("Tenant ID not found in request context")
        
        query = db.query(SocialPost).filter(
            SocialPost.tenant_id == tenant_id,
            SocialPost.status == PostStatus.SCHEDULED
        )
        
        if account_id:
            query = query.filter(SocialPost.social_account_id == account_id)
        
        if start_date:
            query = query.filter(SocialPost.scheduled_at >= start_date)
        
        if end_date:
            query = query.filter(SocialPost.scheduled_at <= end_date)
        
        return query.order_by(SocialPost.scheduled_at.asc()).all()
