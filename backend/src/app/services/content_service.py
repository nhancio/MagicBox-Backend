"""
Content Service - Orchestrates AI content generation and social media publishing.
High-level service that combines AI generation with publishing workflows.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.ai_service import AIService
from app.services.social_service import SocialService
from app.db.models.artifact import Artifact, ArtifactType, ArtifactStatus
from app.db.models.social_post import SocialPost, PostStatus
from app.db.models.social_account import SocialPlatform
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID
import uuid


class ContentService:
    """High-level service for content creation and publishing workflows."""
    
    @staticmethod
    def generate_and_create_post(
        db: Session,
        topic: str,
        platform: SocialPlatform,
        tone: str = "professional",
        target_audience: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI content and create an artifact.
        
        Args:
            db: Database session
            topic: Content topic
            platform: Target social media platform
            tone: Content tone
            target_audience: Target audience description
            project_id: Optional project ID
        
        Returns:
            Dict with artifact and generated content
        """
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id or not user_id:
            raise ValueError("Tenant ID and User ID must be in request context")
        
        # Generate content using AI
        platform_name = platform.value.lower()
        ai_result = AIService.generate_post(
            topic=topic,
            tone=tone,
            target_audience=target_audience,
            platform=platform_name,
        )
        
        if not ai_result.get("success"):
            raise ValueError(f"AI generation failed: {ai_result.get('error')}")
        
        # Create artifact
        artifact = Artifact(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            user_id=user_id,
            type=ArtifactType.POST,
            status=ArtifactStatus.DRAFT,
            content=ai_result.get("content", ""),
            extra_metadata={
                "hashtags": ai_result.get("hashtags", []),
                "key_points": ai_result.get("key_points", []),
                "platform": platform_name,
                "tone": tone,
                "ai_generated": True,
            }
        )
        
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        
        return {
            "artifact": artifact,
            "generated_content": ai_result,
        }
    
    @staticmethod
    def generate_reel_script(
        db: Session,
        topic: str,
        duration_seconds: int = 30,
        style: str = "engaging",
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a reel/short script and create artifact."""
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id or not user_id:
            raise ValueError("Tenant ID and User ID must be in request context")
        
        # Generate script
        ai_result = AIService.generate_reel_script(
            topic=topic,
            duration_seconds=duration_seconds,
            style=style,
        )
        
        if not ai_result.get("success"):
            raise ValueError(f"AI generation failed: {ai_result.get('error')}")
        
        # Create artifact
        artifact = Artifact(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            user_id=user_id,
            type=ArtifactType.REEL,
            status=ArtifactStatus.DRAFT,
            content=ai_result.get("script", ""),
            extra_metadata={
                "hook": ai_result.get("hook", ""),
                "scenes": ai_result.get("scenes", []),
                "call_to_action": ai_result.get("call_to_action", ""),
                "duration_seconds": duration_seconds,
                "style": style,
                "ai_generated": True,
            }
        )
        
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        
        return {
            "artifact": artifact,
            "script": ai_result,
        }
    
    @staticmethod
    def generate_video_script(
        db: Session,
        topic: str,
        duration_minutes: int = 5,
        format: str = "tutorial",
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a video script and create artifact."""
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id or not user_id:
            raise ValueError("Tenant ID and User ID must be in request context")
        
        # Generate script
        ai_result = AIService.generate_video_script(
            topic=topic,
            duration_minutes=duration_minutes,
            format=format,
        )
        
        if not ai_result.get("success"):
            raise ValueError(f"AI generation failed: {ai_result.get('error')}")
        
        # Create artifact
        artifact = Artifact(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            user_id=user_id,
            type=ArtifactType.VIDEO,
            status=ArtifactStatus.DRAFT,
            content=ai_result.get("full_script", ""),
            extra_metadata={
                "introduction": ai_result.get("introduction", ""),
                "sections": ai_result.get("sections", []),
                "conclusion": ai_result.get("conclusion", ""),
                "timestamps": ai_result.get("timestamps", []),
                "duration_minutes": duration_minutes,
                "format": format,
                "ai_generated": True,
            }
        )
        
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        
        return {
            "artifact": artifact,
            "script": ai_result,
        }
    
    @staticmethod
    def publish_artifact_to_social(
        db: Session,
        artifact_id: str,
        social_account_id: str,
        scheduled_at: Optional[datetime] = None,
        custom_content: Optional[str] = None,
    ) -> SocialPost:
        """
        Publish an artifact to a social media platform.
        
        Args:
            db: Database session
            artifact_id: Artifact ID to publish
            social_account_id: Social account to publish to
            scheduled_at: Optional scheduled time
            custom_content: Optional custom content (overrides artifact content)
        
        Returns:
            Created SocialPost
        """
        tenant_id = get_context(CTX_TENANT_ID)
        
        if not tenant_id:
            raise ValueError("Tenant ID not found in request context")
        
        # Get artifact
        artifact = db.query(Artifact).filter(
            Artifact.id == artifact_id,
            Artifact.tenant_id == tenant_id
        ).first()
        
        if not artifact:
            raise ValueError("Artifact not found")
        
        # Use custom content or artifact content
        content = custom_content or artifact.content or ""
        
        # Get media URLs from artifact if available
        media_urls = []
        if artifact.image_url:
            media_urls.append(artifact.image_url)
        if artifact.video_url:
            media_urls.append(artifact.video_url)
        
        # Publish
        post = SocialService.publish_post(
            db=db,
            account_id=social_account_id,
            content=content,
            media_urls=media_urls if media_urls else None,
            scheduled_at=scheduled_at,
        )
        
        # Link artifact to post
        post.artifact_id = artifact_id
        db.commit()
        
        return post
    
    @staticmethod
    def publish_to_multiple_platforms(
        db: Session,
        artifact_id: str,
        social_account_ids: List[str],
        scheduled_at: Optional[datetime] = None,
        custom_content: Optional[str] = None,
    ) -> List[SocialPost]:
        """Publish an artifact to multiple social media platforms."""
        posts = []
        
        for account_id in social_account_ids:
            try:
                post = ContentService.publish_artifact_to_social(
                    db=db,
                    artifact_id=artifact_id,
                    social_account_id=account_id,
                    scheduled_at=scheduled_at,
                    custom_content=custom_content,
                )
                posts.append(post)
            except Exception as e:
                # Log error but continue with other platforms
                print(f"Failed to publish to account {account_id}: {e}")
                continue
        
        return posts
