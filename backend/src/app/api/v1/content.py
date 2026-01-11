"""
Content Generation API endpoints - AI-powered content creation.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.services.content_service import ContentService
from app.services.ai_service import AIService
from app.db.models.social_account import SocialPlatform
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/projects/{project_id}/content", tags=["Content Generation"])


# Request Schemas
class GeneratePostRequest(BaseModel):
    topic: str = Field(..., description="Content topic", example="5 Tips for Small Business Marketing")
    tone: str = Field(default="professional", description="Content tone", example="professional")
    target_audience: Optional[str] = Field(None, description="Target audience", example="small business owners")
    project_id: Optional[str] = Field(None, description="Project ID")


class GenerateReelRequest(BaseModel):
    topic: str = Field(..., description="Reel topic", example="Quick Marketing Tips")
    duration_seconds: int = Field(default=30, description="Duration in seconds", example=30)
    style: str = Field(default="engaging", description="Content style", example="engaging")
    project_id: Optional[str] = Field(None, description="Project ID")


class GenerateVideoRequest(BaseModel):
    topic: str = Field(..., description="Video topic", example="Complete Guide to Social Media Marketing")
    duration_minutes: int = Field(default=5, description="Duration in minutes", example=5)
    format: str = Field(default="tutorial", description="Video format", example="tutorial")
    sections: Optional[List[str]] = Field(None, description="Sections to cover")
    project_id: Optional[str] = Field(None, description="Project ID")


class OptimizeContentRequest(BaseModel):
    content: str = Field(..., description="Content to optimize")
    platform: str = Field(..., description="Target platform", example="instagram")
    current_format: Optional[str] = Field(None, description="Current format")


# Endpoints
@router.post("/generate/post", status_code=status.HTTP_201_CREATED)
def generate_post(
    project_id: str,
    request: GeneratePostRequest,
    platform: str = "general",
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Generate AI-powered social media post content.
    Requires authentication and a project.
    """
    try:
        platform_enum = SocialPlatform[platform.upper()] if platform.upper() in [p.name for p in SocialPlatform] else None
        
        result = ContentService.generate_and_create_post(
            db=db,
            topic=request.topic,
            platform=platform_enum or SocialPlatform.FACEBOOK,
            tone=request.tone,
            target_audience=request.target_audience,
            project_id=request.project_id or current_project.id,
        )
        
        return {
            "success": True,
            "artifact_id": result["artifact"].id,
            "content": result["generated_content"]["content"],
            "hashtags": result["generated_content"].get("hashtags", []),
            "metadata": result["generated_content"].get("metadata", {}),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )


@router.post("/generate/reel", status_code=status.HTTP_201_CREATED)
def generate_reel_script(
    request: GenerateReelRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Generate AI-powered reel/short script.
    Requires authentication and a project.
    """
    try:
        result = ContentService.generate_reel_script(
            db=db,
            topic=request.topic,
            duration_seconds=request.duration_seconds,
            style=request.style,
            project_id=request.project_id or current_project.id,
        )
        
        return {
            "success": True,
            "artifact_id": result["artifact"].id,
            "script": result["script"]["script"],
            "hook": result["script"].get("hook", ""),
            "scenes": result["script"].get("scenes", []),
            "call_to_action": result["script"].get("call_to_action", ""),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate reel script: {str(e)}"
        )


@router.post("/generate/video", status_code=status.HTTP_201_CREATED)
def generate_video_script(
    request: GenerateVideoRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Generate AI-powered video script.
    Requires authentication and a project.
    """
    try:
        result = ContentService.generate_video_script(
            db=db,
            topic=request.topic,
            duration_minutes=request.duration_minutes,
            format=request.format,
            project_id=request.project_id or current_project.id,
        )
        
        return {
            "success": True,
            "artifact_id": result["artifact"].id,
            "script": result["script"]["full_script"],
            "sections": result["script"].get("sections", []),
            "timestamps": result["script"].get("timestamps", []),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate video script: {str(e)}"
        )


@router.post("/optimize")
def optimize_content(
    request: OptimizeContentRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Optimize content for a specific platform.
    Requires authentication and a project.
    """
    try:
        result = AIService.optimize_content_for_platform(
            content=request.content,
            platform=request.platform,
            current_format=request.current_format,
        )
        
        if not result.get("success"):
            raise ValueError(result.get("error", "Optimization failed"))
        
        return {
            "success": True,
            "original_content": result["original_content"],
            "optimized_content": result["optimized_content"],
            "recommendations": result.get("recommendations", []),
            "best_practices": result.get("best_practices", []),
            "character_count": result.get("character_count", 0),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize content: {str(e)}"
        )


@router.post("/hashtags")
def generate_hashtags(
    topic: str,
    platform: str = "instagram",
    count: int = 10,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Generate relevant hashtags for a topic.
    Requires authentication and a project.
    """
    try:
        result = AIService.generate_hashtags(
            topic=topic,
            platform=platform,
            count=count,
        )
        
        if not result.get("success"):
            raise ValueError(result.get("error", "Hashtag generation failed"))
        
        return {
            "success": True,
            "hashtags": result.get("hashtags", []),
            "categories": result.get("categories", {}),
            "platform": platform,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate hashtags: {str(e)}"
        )
