"""
Social Media API endpoints - Account management and publishing.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.services.social_service import SocialService
from app.services.content_service import ContentService
from app.db.models.social_account import SocialPlatform
from app.db.models.social_post import PostStatus
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/projects/{project_id}/social", tags=["Social Media"])


# Request Schemas
class ConnectAccountRequest(BaseModel):
    platform: str = Field(..., description="Social media platform", example="FACEBOOK")
    account_name: str = Field(..., description="Account display name", example="My Business Page")
    access_token: str = Field(..., description="OAuth access token")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")
    account_id: Optional[str] = Field(None, description="Platform-specific account ID")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class PublishPostRequest(BaseModel):
    account_id: str = Field(..., description="Social account ID to publish to")
    content: str = Field(..., description="Post content")
    media_urls: Optional[List[str]] = Field(None, description="Media URLs")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled publish time")


class PublishArtifactRequest(BaseModel):
    artifact_id: str = Field(..., description="Artifact ID to publish")
    account_id: str = Field(..., description="Social account ID")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled publish time")
    custom_content: Optional[str] = Field(None, description="Custom content (overrides artifact)")


class PublishToMultipleRequest(BaseModel):
    artifact_id: str = Field(..., description="Artifact ID to publish")
    account_ids: List[str] = Field(..., description="List of social account IDs")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled publish time")
    custom_content: Optional[str] = Field(None, description="Custom content")


# Endpoints
@router.post("/accounts/connect", status_code=status.HTTP_201_CREATED)
def connect_account(
    project_id: str,
    request: ConnectAccountRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Connect a social media account.
    Requires authentication and a project.
    """
    try:
        platform = SocialPlatform[request.platform.upper()]
        
        account = SocialService.connect_account(
            db=db,
            platform=platform,
            account_name=request.account_name,
            access_token=request.access_token,
            refresh_token=request.refresh_token,
            account_id=request.account_id,
            metadata=request.metadata,
        )
        
        return {
            "success": True,
            "account_id": account.id,
            "platform": account.platform.value,
            "account_name": account.account_name,
            "is_connected": account.is_connected,
        }
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform. Available: {[p.name for p in SocialPlatform]}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to connect account: {str(e)}"
        )


@router.get("/accounts")
def list_accounts(
    platform: Optional[str] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    List connected social media accounts.
    Requires authentication and a project.
    """
    try:
        platform_enum = None
        if platform:
            platform_enum = SocialPlatform[platform.upper()]
        
        accounts = SocialService.list_accounts(
            db=db,
            platform=platform_enum,
            active_only=active_only,
        )
        
        return {
            "success": True,
            "accounts": [
                {
                    "id": acc.id,
                    "platform": acc.platform.value,
                    "account_name": acc.account_name,
                    "is_connected": acc.is_connected,
                    "is_active": acc.is_active,
                    "created_at": acc.created_at.isoformat() if acc.created_at else None,
                }
                for acc in accounts
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list accounts: {str(e)}"
        )


@router.delete("/accounts/{account_id}")
def disconnect_account(
    account_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Disconnect a social media account.
    Requires authentication and a project.
    """
    try:
        success = SocialService.disconnect_account(db=db, account_id=account_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        return {"success": True, "message": "Account disconnected"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect account: {str(e)}"
        )


@router.post("/publish", status_code=status.HTTP_201_CREATED)
def publish_post(
    request: PublishPostRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Publish a post directly to a social media platform.
    Requires authentication and a project.
    """
    try:
        post = SocialService.publish_post(
            db=db,
            account_id=request.account_id,
            content=request.content,
            media_urls=request.media_urls,
            scheduled_at=request.scheduled_at,
        )
        
        return {
            "success": True,
            "post_id": post.id,
            "status": post.status.value,
            "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else None,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "external_url": post.external_url,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish post: {str(e)}"
        )


@router.post("/publish/artifact", status_code=status.HTTP_201_CREATED)
def publish_artifact(
    request: PublishArtifactRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Publish an artifact to a social media platform.
    Requires authentication and a project.
    """
    try:
        post = ContentService.publish_artifact_to_social(
            db=db,
            artifact_id=request.artifact_id,
            social_account_id=request.account_id,
            scheduled_at=request.scheduled_at,
            custom_content=request.custom_content,
        )
        
        return {
            "success": True,
            "post_id": post.id,
            "artifact_id": post.artifact_id,
            "status": post.status.value,
            "external_url": post.external_url,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish artifact: {str(e)}"
        )


@router.post("/publish/multiple", status_code=status.HTTP_201_CREATED)
def publish_to_multiple(
    request: PublishToMultipleRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Publish an artifact to multiple social media platforms.
    Requires authentication and a project.
    """
    try:
        posts = ContentService.publish_to_multiple_platforms(
            db=db,
            artifact_id=request.artifact_id,
            social_account_ids=request.account_ids,
            scheduled_at=request.scheduled_at,
            custom_content=request.custom_content,
        )
        
        return {
            "success": True,
            "posts": [
                {
                    "post_id": post.id,
                    "account_id": post.social_account_id,
                    "status": post.status.value,
                    "external_url": post.external_url,
                }
                for post in posts
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish to multiple platforms: {str(e)}"
        )


@router.get("/posts/{post_id}/analytics")
def get_post_analytics(
    post_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Get analytics for a published post.
    Requires authentication and a project.
    """
    try:
        analytics = SocialService.get_post_analytics(db=db, post_id=post_id)
        
        return {
            "success": True,
            "analytics": analytics,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/posts")
def list_posts(
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    List social media posts.
    Requires authentication and a project.
    """
    from app.db.models.social_post import SocialPost
    
    tenant_id = current_user.tenant_id
    
    query = db.query(SocialPost).filter(
        SocialPost.tenant_id == tenant_id
    )
    
    if account_id:
        query = query.filter(SocialPost.social_account_id == account_id)
    
    if status:
        try:
            status_enum = PostStatus[status.upper()]
            query = query.filter(SocialPost.status == status_enum)
        except KeyError:
            pass
    
    posts = query.order_by(SocialPost.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "posts": [
            {
                "id": post.id,
                "content": post.content[:100] + "..." if len(post.content) > 100 else post.content,
                "status": post.status.value,
                "platform": None,  # Would need to join with social_account
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "external_url": post.external_url,
                "metrics": {
                    "likes": post.likes_count,
                    "comments": post.comments_count,
                    "shares": post.shares_count,
                    "views": post.views_count,
                }
            }
            for post in posts
        ]
    }
