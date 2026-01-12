"""
Test Generation API - Quick test endpoints for image/post/reel generation.
For testing purposes only.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import tempfile
import json

from app.db.session import get_db
from app.db.models.user import User
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/test", tags=["Test Generation"])


class TestImageRequest(BaseModel):
    prompt: str = Field(..., description="Image generation prompt", example="A vibrant coffee shop promotion image with warm colors")


class TestPostRequest(BaseModel):
    topic: str = Field(..., description="Post topic", example="New product launch for small business")
    tone: Optional[str] = Field("professional", description="Tone of voice")
    platform: Optional[str] = Field(None, description="Target platform")
    generate_image: Optional[bool] = Field(True, description="Also generate image for the post (default: True)")


class TestReelRequest(BaseModel):
    topic: str = Field(..., description="Reel topic", example="Product demonstration for marketing")
    duration_seconds: Optional[int] = Field(30, description="Duration in seconds")
    generate_video: Optional[bool] = Field(True, description="Generate video using Veo 3.1 (default: True)")


@router.post("/image", status_code=status.HTTP_200_OK)
def test_image_generation(
    request: TestImageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Test image generation using Gemini 2.5 Flash Image."""
    try:
        from app.services.ai_image_service import AIImageService
        
        result = AIImageService.generate_image(
            prompt=request.prompt,
            output_path=None,
        )
        
        return {
            "success": result.get("success", False),
            "image_path": result.get("image_path"),
            "prompt": request.prompt,
            "metadata": result.get("metadata", {}),
            "error": result.get("error") if not result.get("success") else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate image: {str(e)}"
        )


@router.post("/post", status_code=status.HTTP_200_OK)
def test_post_generation(
    request: TestPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Test post generation using Gemini 3 Pro.
    By default also generates an image for the post using Gemini 2.5 Flash Image.
    """
    try:
        from app.services.ai_service import AIService
        from app.services.ai_image_service import AIImageService
        
        result = AIService.generate_post(
            topic=request.topic,
            tone=request.tone or "professional",
            platform=request.platform,
        )
        
        # Save post to temp file
        temp_dir = Path(tempfile.gettempdir())
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_filename = f"generated_post_{abs(hash(request.topic))}.txt"
        temp_path = temp_dir / temp_filename
        
        # Format post content for file
        post_content = f"""Generated Social Media Post
========================

Content:
{result.get("content", "")}

Caption:
{result.get("caption", "")}

Hashtags:
{', '.join(result.get("hashtags", []))}

Key Points:
{chr(10).join(f"- {point}" for point in result.get("key_points", []))}

Platform: {result.get("platform", "general")}
Tone: {request.tone or "professional"}
"""
        
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(post_content)
        
        # Also save as JSON
        json_path = temp_dir / f"generated_post_{abs(hash(request.topic))}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        response = {
            "success": True,
            "content": result.get("content"),
            "hashtags": result.get("hashtags", []),
            "caption": result.get("caption"),
            "key_points": result.get("key_points", []),
            "platform": result.get("platform"),
            "post_file_path": str(temp_path),
            "json_path": str(json_path),
            "metadata": result.get("metadata", {}),
        }
        
        # Generate image for the post (default: True)
        if request.generate_image:
            # Build image prompt from post content
            image_prompt = f"Marketing image for social media post about: {request.topic}. Style: {request.tone or 'professional'}. Platform: {request.platform or 'social media'}. Create a visually appealing image that complements this content: {result.get('content', '')[:200]}"
            
            image_result = AIImageService.generate_image(
                prompt=image_prompt,
                output_path=None,
            )
            
            response["image"] = {
                "success": image_result.get("success", False),
                "image_path": image_result.get("image_path"),
                "prompt": image_prompt,
                "error": image_result.get("error") if not image_result.get("success") else None,
            }
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate post: {str(e)}"
        )


@router.post("/reel", status_code=status.HTTP_200_OK)
def test_reel_generation(
    request: TestReelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Test reel/shorts generation.
    1. Generates script using Gemini 3 Pro
    2. Generates actual video using Veo 3.1 (by default)
    
    Note: Video generation may take 1-2 minutes as Veo 3.1 creates actual video content.
    """
    try:
        from app.services.ai_service import AIService
        from app.services.ai_video_service import AIVideoService
        
        # Generate script
        script_result = AIService.generate_reel_script(
            topic=request.topic,
            duration_seconds=request.duration_seconds or 30,
        )
        
        # Save script to temp file
        temp_dir = Path(tempfile.gettempdir())
        temp_dir.mkdir(parents=True, exist_ok=True)
        script_filename = f"generated_reel_script_{abs(hash(request.topic))}.txt"
        script_path = temp_dir / script_filename
        
        # Format script content for file
        script_content = f"""Generated Reel Script ({request.duration_seconds or 30} seconds)
==========================================

Hook:
{script_result.get("hook", "")}

Script:
{script_result.get("script", "")}

Scenes:
{chr(10).join(f"{i+1}. {scene}" if isinstance(scene, str) else f"{i+1}. {json.dumps(scene, indent=2)}" for i, scene in enumerate(script_result.get("scenes", [])))}

Call to Action:
{script_result.get("call_to_action", "")}
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Also save as JSON
        json_path = temp_dir / f"generated_reel_{abs(hash(request.topic))}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(script_result, f, indent=2, ensure_ascii=False)
        
        response = {
            "success": script_result.get("success", False),
            "script": script_result.get("script"),
            "hook": script_result.get("hook"),
            "scenes": script_result.get("scenes", []),
            "call_to_action": script_result.get("call_to_action"),
            "script_file_path": str(script_path),
            "json_path": str(json_path),
            "metadata": script_result.get("metadata", {}),
        }
        
        # Generate video (default is True)
        if request.generate_video:
            # Build base prompt from script
            video_prompt = f"""Create a short marketing video:
Hook: {script_result.get('hook', '')}
Main content: {script_result.get('script', '')[:500]}
Style: Professional, engaging, suitable for social media marketing.
"""
            
            # Prepare script data for scene planning
            script_data = {
                "hook": script_result.get("hook", ""),
                "script": script_result.get("script", ""),
                "scenes": script_result.get("scenes", []),
                "call_to_action": script_result.get("call_to_action", ""),
            }
            
            print(f"Generating {request.duration_seconds or 30}-second video with Veo 3.1...")
            print(f"This will create multiple scenes and stitch them together. This may take 5-10 minutes.")
            
            video_result = AIVideoService.generate_video(
                prompt=video_prompt,
                output_path=None,  # Will save to temp directory
                duration_seconds=request.duration_seconds or 30,
                script_data=script_data,  # Pass script data for better scene planning
            )
            
            response["video"] = {
                "success": video_result.get("success", False),
                "video_path": video_result.get("video_path"),
                "prompt_used": video_prompt[:200] + "...",
                "metadata": video_result.get("metadata", {}),
                "error": video_result.get("error") if not video_result.get("success") else None,
            }
        else:
            response["video"] = {
                "success": False,
                "message": "Video generation was disabled (generate_video=false)",
                "video_path": None,
            }
        
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate reel: {str(e)}"
        )
