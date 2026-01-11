"""
AI Video Generation Service - Using Veo 3.1 for video/reel generation.
"""
from typing import Optional, Dict, Any
from app.config.settings import settings
import time

# Optional import for new Google Genai SDK
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None


class AIVideoService:
    """Service for AI-powered video generation using Veo 3.1."""
    
    _client: Optional[Any] = None
    
    @classmethod
    def _get_client(cls):
        """Initialize and return Gemini client."""
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai not installed. Install: pip install google-genai")
        
        if cls._client is None:
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured in environment variables")
            cls._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return cls._client
    
    @staticmethod
    def generate_video(
        prompt: str,
        output_path: Optional[str] = None,
        poll_interval: int = 10,
    ) -> Dict[str, Any]:
        """
        Generate a video using Veo 3.1 model.
        
        Args:
            prompt: Video generation prompt (detailed scene description)
            output_path: Optional path to save the video
            poll_interval: Seconds between polling for completion
        
        Returns:
            Dict with video path, operation status, and metadata
        """
        try:
            client = AIVideoService._get_client()
            
            # Start video generation with veo-3.1-generate-preview
            operation = client.models.generate_videos(
                model="veo-3.1-generate-preview",
                prompt=prompt,
            )
            
            # Poll the operation status until the video is ready
            while not operation.done:
                print(f"Waiting for video generation to complete... (operation: {operation.name})")
                time.sleep(poll_interval)
                operation = client.operations.get(operation)
            
            if not operation.response or not operation.response.generated_videos:
                return {
                    "success": False,
                    "error": "No video generated in response",
                    "video_path": None
                }
            
            # Download the generated video
            generated_video = operation.response.generated_videos[0]
            video_file = client.files.download(file=generated_video.video)
            
            # Save video if output_path provided
            if output_path:
                video_file.save(output_path)
                saved_path = output_path
            else:
                # Save to temporary location
                from pathlib import Path
                temp_path = Path(f"/tmp/generated_video_{hash(prompt)}.mp4")
                video_file.save(str(temp_path))
                saved_path = str(temp_path)
            
            return {
                "success": True,
                "video_path": saved_path,
                "video_file": video_file,
                "prompt": prompt,
                "operation_name": operation.name,
                "metadata": {
                    "model": "veo-3.1-generate-preview",
                    "duration_seconds": getattr(generated_video, 'duration_seconds', None),
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "video_path": None
            }
