"""
Publishing Tasks - Celery tasks for scheduled post publishing.
"""
from datetime import datetime, timedelta
import uuid
from app.db.session import SessionLocal
from app.services.social_service import SocialService
from app.db.models.social_post import SocialPost, PostStatus
from app.db.models.social_account import SocialAccount

# Import Celery app from central configuration
from app.celery_app import celery_app


@celery_app.task(name='publish_scheduled_post')
def publish_scheduled_post(post_id: str):
    """
    Publish a scheduled post.
    This task is executed at the scheduled time.
    
    Args:
        post_id: SocialPost ID to publish
    """
    db = SessionLocal()
    try:
        # Get the post
        post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
        
        if not post:
            print(f"Post {post_id} not found")
            return
        
        # Check if already published or cancelled
        if post.status != PostStatus.SCHEDULED:
            print(f"Post {post_id} is not in SCHEDULED status: {post.status}")
            return
        
        # Get social account
        account = db.query(SocialAccount).filter(
            SocialAccount.id == post.social_account_id
        ).first()
        
        if not account or not account.is_connected:
            post.status = PostStatus.FAILED
            post.error_message = "Social account not connected"
            db.commit()
            return
        
        # Publish the post
        try:
            SocialService._publish_now(db, post, account)
            print(f"Successfully published post {post_id}")
            
            # If recurring, create next occurrence
            if post.extra_metadata and post.extra_metadata.get("is_recurring"):
                try:
                    _create_next_recurrence(db, post)
                except Exception as e:
                    print(f"Failed to create next recurrence: {e}")
                
        except Exception as e:
            post.status = PostStatus.FAILED
            post.error_message = str(e)
            post.retry_count += 1
            db.commit()
            print(f"Failed to publish post {post_id}: {e}")
            
    except Exception as e:
        print(f"Error in publish_scheduled_post task: {e}")
    finally:
        db.close()


def _create_next_recurrence(db, post: SocialPost):
    """Create the next occurrence for a recurring post."""
    from app.tasks.notification_tasks import send_pre_post_notification
    
    metadata = post.extra_metadata or {}
    pattern = metadata.get("recurrence_pattern")
    end_date_str = metadata.get("recurrence_end_date")
    
    if not pattern:
        return
    
    # Calculate next occurrence
    current_scheduled = post.scheduled_at
    if pattern == "daily":
        next_scheduled = current_scheduled + timedelta(days=1)
    elif pattern == "weekly":
        next_scheduled = current_scheduled + timedelta(weeks=1)
    elif pattern == "monthly":
        next_scheduled = current_scheduled + timedelta(days=30)
    else:
        return
    
    # Check end date
    if end_date_str:
        end_date = datetime.fromisoformat(end_date_str)
        if next_scheduled > end_date:
            return
    
    # Create new post
    new_post = SocialPost(
        id=str(uuid.uuid4()),
        tenant_id=post.tenant_id,
        social_account_id=post.social_account_id,
        content=post.content,
        media_urls=post.media_urls,
        status=PostStatus.SCHEDULED,
        scheduled_at=next_scheduled,
        created_by=post.created_by,
        extra_metadata=metadata,
    )
    
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    # Schedule notification and publishing
    notify_hours = metadata.get("notify_before_hours", 1)
    user_phone = metadata.get("user_phone")
    
    if user_phone:
        notification_time = next_scheduled - timedelta(hours=notify_hours)
        if notification_time > datetime.utcnow():
            try:
                from app.tasks.notification_tasks import send_pre_post_notification
                send_pre_post_notification.apply_async(
                    args=[new_post.id, user_phone],
                    eta=notification_time
                )
            except Exception as e:
                print(f"Failed to schedule notification for recurrence: {e}")
    
    try:
        publish_scheduled_post.apply_async(
            args=[new_post.id],
            eta=next_scheduled
        )
    except Exception as e:
        print(f"Failed to schedule next recurrence: {e}")
