"""
Notification Tasks - Celery tasks for sending WhatsApp notifications.
"""
from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.db.models.social_post import SocialPost, PostStatus
from app.db.models.social_account import SocialAccount
from app.integrations.whatsapp import WhatsAppIntegration

# Import Celery app from central configuration
from app.celery_app import celery_app


@celery_app.task(name='send_pre_post_notification')
def send_pre_post_notification(post_id: str, phone_number: str):
    """
    Send WhatsApp notification 1 hour before scheduled post.
    
    Args:
        post_id: SocialPost ID
        phone_number: User's WhatsApp number
    """
    db = SessionLocal()
    try:
        # Get the post
        post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
        
        if not post:
            print(f"Post {post_id} not found for notification")
            return
        
        # Check if post is still scheduled
        if post.status != PostStatus.SCHEDULED:
            print(f"Post {post_id} is no longer scheduled, skipping notification")
            return
        
        # Get social account for platform info
        account = db.query(SocialAccount).filter(
            SocialAccount.id == post.social_account_id
        ).first()
        
        platform = account.platform.value if account else "Social Media"
        
        # Format scheduled time
        scheduled_time = post.scheduled_at.strftime("%Y-%m-%d %H:%M %Z") if post.scheduled_at else "Unknown"
        
        # Get post preview (first 50 chars)
        post_title = post.content[:50] + "..." if len(post.content) > 50 else post.content
        
        # Send WhatsApp notification
        try:
            whatsapp = WhatsAppIntegration()
            formatted_phone = WhatsAppIntegration.format_phone_number(phone_number)
            
            result = whatsapp.send_notification(
                phone_number=formatted_phone,
                post_title=post_title,
                scheduled_time=scheduled_time,
                platform=platform,
            )
            
            print(f"Notification sent to {formatted_phone} for post {post_id}")
            
            # Store notification status in post metadata
            if not post.extra_metadata:
                post.extra_metadata = {}
            post.extra_metadata["notification_sent"] = True
            post.extra_metadata["notification_sent_at"] = datetime.utcnow().isoformat()
            db.commit()
            
        except Exception as e:
            print(f"Failed to send WhatsApp notification for post {post_id}: {e}")
            # Log error but don't fail the task
            
    except Exception as e:
        print(f"Error in send_pre_post_notification task: {e}")
    finally:
        db.close()
