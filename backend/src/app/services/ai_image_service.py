"""
AI Image Generation Service - Using Gemini 2.5 Flash Image model.
"""
from typing import Optional, Dict, Any
from app.config.settings import settings
from pathlib import Path
import io

# Optional import for new Google Genai SDK
try:
    from google import genai
    from google.genai import types
    from PIL import Image
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None
    Image = None


class AIImageService:
    """Service for AI-powered image generation using Gemini 2.5 Flash Image."""
    
    _client: Optional[Any] = None
    
    @classmethod
    def _get_client(cls):
        """Initialize and return Gemini client."""
        if not GEMINI_AVAILABLE:
            raise ImportError("google-genai not installed. Install: pip install google-genai pillow")
        
        if cls._client is None:
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured in environment variables")
            cls._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return cls._client
    
    @staticmethod
    def generate_image(
        prompt: str,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate an image using Gemini 2.5 Flash Image model.
        
        Args:
            prompt: Image generation prompt
            output_path: Optional path to save the image (if not provided, returns image data)
        
        Returns:
            Dict with image path, image data, and metadata
        """
        try:
            client = AIImageService._get_client()
            
            # Use gemini-2.5-flash-image for image generation
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt],
            )
            
            image_data = None
            saved_path = None
            
            # Process response parts
            for part in response.parts:
                if part.text is not None:
                    # Text response (if any)
                    continue
                elif part.inline_data is not None:
                    # Image data
                    image = part.as_image()
                    image_data = image
                    
                    # Save if output_path provided
                    if output_path:
                        image.save(output_path)
                        saved_path = output_path
                    else:
                        # Save to temporary location
                        temp_path = Path(f"/tmp/generated_image_{hash(prompt)}.png")
                        image.save(str(temp_path))
                        saved_path = str(temp_path)
            
            if not image_data:
                return {
                    "success": False,
                    "error": "No image generated in response",
                    "image_path": None
                }
            
            return {
                "success": True,
                "image_path": saved_path,
                "image": image_data,
                "prompt": prompt,
                "metadata": {
                    "model": "gemini-2.5-flash-image",
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "image_path": None
            }
