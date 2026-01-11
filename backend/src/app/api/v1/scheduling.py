"""
Scheduling API endpoints - Schedule posts with WhatsApp notifications.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.services.scheduling_service import SchedulingService
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/scheduling", tags=["Scheduling"])


class SchedulePostRequest(BaseModel):
    account_id: str = Field(..., description="Social account ID to post to")
    content: str = Field(..., description="Post content")
    scheduled_at: datetime = Field(..., description="When to publish (ISO format)")
    media_urls: Optional[List[str]] = Field(None, description="Media URLs")
    notify_before_hours: int = Field(default=1, description="Hours before post to send notification")
    user_phone: Optional[str] = Field(None, description="User's WhatsApp number for notifications")


class RecurringScheduleRequest(BaseModel):
    account_id: str = Field(..., description="Social account ID to post to")
    content: str = Field(..., description="Post content")
    start_date: datetime = Field(..., description="When to start the schedule")
    time_of_day: str = Field(..., description="Time of day to post (HH:MM format)", example="09:00")
    recurrence_pattern: str = Field(..., description="Recurrence pattern: daily, weekly, or monthly", example="daily")
    recurrence_end_date: Optional[datetime] = Field(None, description="When to stop recurring")
    notify_before_hours: int = Field(default=1, description="Hours before post to send notification")
    user_phone: Optional[str] = Field(None, description="User's WhatsApp number for notifications")


@router.post("/schedule", status_code=status.HTTP_201_CREATED)
def schedule_post(
    request: SchedulePostRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Schedule a post for future publishing.
    Sends WhatsApp notification 1 hour before (if phone number provided).
    
    Requires authentication and a project.
    """
    try:
        # Get user's phone number if not provided
        user_phone = request.user_phone
        if not user_phone and hasattr(current_user, 'phone_number'):
            user_phone = current_user.phone_number
        
        post = SchedulingService.schedule_post(
            db=db,
            account_id=request.account_id,
            content=request.content,
            scheduled_at=request.scheduled_at,
            media_urls=request.media_urls,
            notify_before_hours=request.notify_before_hours,
            user_phone=user_phone,
        )
        
        return {
            "success": True,
            "post_id": post.id,
            "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
            "status": post.status.value,
            "notification_scheduled": user_phone is not None,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to schedule post: {str(e)}"
        )


@router.post("/recurring", status_code=status.HTTP_201_CREATED)
def create_recurring_schedule(
    request: RecurringScheduleRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Create a recurring schedule for posts (e.g., every morning at 9 AM).
    Sends WhatsApp notification 1 hour before each post.
    
    Requires authentication and a project.
    """
    try:
        # Validate recurrence pattern
        if request.recurrence_pattern not in ["daily", "weekly", "monthly"]:
            raise ValueError("recurrence_pattern must be 'daily', 'weekly', or 'monthly'")
        
        # Validate time format
        try:
            hour, minute = map(int, request.time_of_day.split(':'))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError("Invalid time format")
        except:
            raise ValueError("time_of_day must be in HH:MM format (e.g., '09:00')")
        
        # Get user's phone number if not provided
        user_phone = request.user_phone
        if not user_phone and hasattr(current_user, 'phone_number'):
            user_phone = current_user.phone_number
        
        posts = SchedulingService.create_recurring_schedule(
            db=db,
            account_id=request.account_id,
            content=request.content,
            start_date=request.start_date,
            time_of_day=request.time_of_day,
            recurrence_pattern=request.recurrence_pattern,
            recurrence_end_date=request.recurrence_end_date,
            notify_before_hours=request.notify_before_hours,
            user_phone=user_phone,
        )
        
        return {
            "success": True,
            "posts_created": len(posts),
            "post_ids": [post.id for post in posts],
            "recurrence_pattern": request.recurrence_pattern,
            "next_post_at": posts[0].scheduled_at.isoformat() if posts else None,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recurring schedule: {str(e)}"
        )


@router.get("/scheduled")
def list_scheduled_posts(
    account_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    List all scheduled posts.
    Requires authentication and a project.
    """
    try:
        posts = SchedulingService.list_scheduled_posts(
            db=db,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        return {
            "success": True,
            "count": len(posts),
            "posts": [
                {
                    "id": post.id,
                    "content": post.content[:100] + "..." if len(post.content) > 100 else post.content,
                    "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
                    "status": post.status.value,
                    "is_recurring": post.extra_metadata.get("is_recurring") if post.extra_metadata else False,
                    "notification_scheduled": post.extra_metadata.get("user_phone") is not None if post.extra_metadata else False,
                }
                for post in posts
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scheduled posts: {str(e)}"
        )


@router.delete("/scheduled/{post_id}")
def cancel_scheduled_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Cancel a scheduled post.
    Requires authentication and a project.
    """
    try:
        success = SchedulingService.cancel_scheduled_post(db=db, post_id=post_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled post not found or already published/cancelled"
            )
        
        return {
            "success": True,
            "message": "Scheduled post cancelled"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel scheduled post: {str(e)}"
        )
