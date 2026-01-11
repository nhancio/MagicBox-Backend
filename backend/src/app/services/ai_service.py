"""
AI Service - Content generation using Google Gemini API.
Handles generation of posts, reels, videos, shorts, and other marketing content.
Uses the new Google Genai SDK (from google import genai).
"""
from typing import Optional, Dict, Any, List
from app.config.settings import settings
import json
import time
from pathlib import Path

# Optional import for new Google Genai SDK
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None


class AIService:
    """Service for AI-powered content generation using Google Gemini."""
    
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
    def generate_post(
        topic: str,
        tone: str = "professional",
        length: str = "medium",
        target_audience: Optional[str] = None,
        platform: Optional[str] = None,
        hashtags: bool = True,
        call_to_action: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a social media post.
        
        Args:
            topic: Main topic/content for the post
            tone: Tone of voice (professional, casual, friendly, etc.)
            length: Post length (short, medium, long)
            target_audience: Target audience description
            platform: Target platform (facebook, instagram, twitter, linkedin, etc.)
            hashtags: Whether to include hashtags
            call_to_action: Optional call to action
        
        Returns:
            Dict with generated content, hashtags, and metadata
        """
        try:
            client = AIService._get_client()
            
            # Build prompt
            prompt = f"""Generate a {tone} social media post about: {topic}

Requirements:
- Length: {length}
- Platform: {platform or 'general social media'}
- Target audience: {target_audience or 'general audience'}
- Include hashtags: {hashtags}
- Call to action: {call_to_action or 'none specified'}

Generate:
1. The main post content (engaging and platform-appropriate)
2. Relevant hashtags (if requested)
3. A suggested caption
4. Key points/messages

Format the response as JSON with keys: content, hashtags, caption, key_points, platform_optimized
"""
            
            # Use gemini-3-pro-preview for text generation
            response = client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=prompt,
            )
            content = response.text
            
            # Try to parse as JSON, fallback to plain text
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, create structured response
                result = {
                    "content": content,
                    "hashtags": [],
                    "caption": content[:200] + "..." if len(content) > 200 else content,
                    "key_points": content.split("\n")[:3],
                    "platform_optimized": platform or "general"
                }
            
            return {
                "success": True,
                "content": result.get("content", content),
                "hashtags": result.get("hashtags", []),
                "caption": result.get("caption", ""),
                "key_points": result.get("key_points", []),
                "platform": platform,
                "tone": tone,
                "metadata": {
                    "model": "gemini-3-pro-preview",
                    "length": length,
                    "target_audience": target_audience
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": None
            }
    
    @staticmethod
    def generate_reel_script(
        topic: str,
        duration_seconds: int = 30,
        style: str = "engaging",
        hook: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate a script for Instagram Reels or TikTok videos.
        
        Args:
            topic: Main topic/content
            duration_seconds: Target duration (15, 30, 60 seconds)
            style: Content style (engaging, educational, entertaining, etc.)
            hook: Opening hook/attention grabber
        
        Returns:
            Dict with script, scenes, and timing
        """
        try:
            client = AIService._get_client()
            
            prompt = f"""Create a {duration_seconds}-second {style} video script (Reel/Short) about: {topic}

Requirements:
- Duration: {duration_seconds} seconds (approximately {duration_seconds * 2.5} words)
- Opening hook: {hook or 'create an attention-grabbing opening'}
- Style: {style}
- Include visual cues and scene descriptions
- Make it engaging and shareable

Format as JSON with:
- hook: Opening line
- scenes: Array of scenes with timing, dialogue, and visual cues
- script: Full script text
- call_to_action: Closing CTA
"""
            
            # Use gemini-3-pro-preview for script generation
            response = client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=prompt,
            )
            content = response.text
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                result = {
                    "hook": hook or f"Let's talk about {topic}",
                    "script": content,
                    "scenes": [],
                    "call_to_action": "Follow for more!"
                }
            
            return {
                "success": True,
                "hook": result.get("hook", ""),
                "script": result.get("script", content),
                "scenes": result.get("scenes", []),
                "call_to_action": result.get("call_to_action", ""),
                "duration_seconds": duration_seconds,
                "style": style,
                "metadata": {
                    "model": "gemini-3-pro-preview",
                    "estimated_word_count": len(content.split())
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "script": None
            }
    
    @staticmethod
    def generate_video_script(
        topic: str,
        duration_minutes: int = 5,
        format: str = "tutorial",
        sections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a script for longer-form videos (YouTube, etc.).
        
        Args:
            topic: Main topic
            duration_minutes: Target duration in minutes
            format: Video format (tutorial, vlog, review, etc.)
            sections: Optional list of sections to cover
        
        Returns:
            Dict with script, sections, and timing
        """
        try:
            client = AIService._get_client()
            
            sections_text = "\n".join([f"- {s}" for s in sections]) if sections else "cover comprehensively"
            
            prompt = f"""Create a {duration_minutes}-minute {format} video script about: {topic}

Requirements:
- Duration: {duration_minutes} minutes (approximately {duration_minutes * 150} words)
- Format: {format}
- Sections to cover:
{sections_text}

Include:
- Engaging introduction
- Clear structure with timestamps
- Key talking points
- Visual/editing cues
- Strong conclusion with CTA

Format as JSON with:
- introduction: Opening segment
- sections: Array of sections with title, content, and estimated_time
- conclusion: Closing segment
- full_script: Complete script text
- timestamps: Array of key timestamps
"""
            
            # Use gemini-3-pro-preview for video script generation
            response = client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=prompt,
            )
            content = response.text
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                result = {
                    "introduction": f"Welcome! Today we're discussing {topic}",
                    "full_script": content,
                    "sections": [],
                    "conclusion": "Thanks for watching!",
                    "timestamps": []
                }
            
            return {
                "success": True,
                "introduction": result.get("introduction", ""),
                "full_script": result.get("full_script", content),
                "sections": result.get("sections", []),
                "conclusion": result.get("conclusion", ""),
                "timestamps": result.get("timestamps", []),
                "duration_minutes": duration_minutes,
                "format": format,
                "metadata": {
                    "model": "gemini-3-pro-preview",
                    "estimated_word_count": len(content.split())
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "script": None
            }
    
    @staticmethod
    def generate_hashtags(
        topic: str,
        platform: str = "instagram",
        count: int = 10,
    ) -> Dict[str, Any]:
        """
        Generate relevant hashtags for a topic.
        
        Args:
            topic: Content topic
            platform: Target platform
            count: Number of hashtags to generate
        
        Returns:
            Dict with hashtags categorized
        """
        try:
            client = AIService._get_client()
            
            prompt = f"""Generate {count} relevant hashtags for: {topic}

Platform: {platform}
Include mix of:
- Popular/broad hashtags
- Niche/specific hashtags
- Trending hashtags (if applicable)

Format as JSON with:
- hashtags: Array of hashtag strings
- categories: Object with category names and their hashtags
"""
            
            # Use gemini-3-pro-preview for hashtag generation
            response = client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=prompt,
            )
            content = response.text
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: extract hashtags from text
                hashtags = [word.strip("#") for word in content.split() if word.startswith("#")]
                result = {
                    "hashtags": hashtags[:count] if hashtags else [topic.replace(" ", "")],
                    "categories": {}
                }
            
            return {
                "success": True,
                "hashtags": result.get("hashtags", []),
                "categories": result.get("categories", {}),
                "platform": platform,
                "count": len(result.get("hashtags", []))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "hashtags": []
            }
    
    @staticmethod
    def optimize_content_for_platform(
        content: str,
        platform: str,
        current_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Optimize existing content for a specific platform.
        
        Args:
            content: Original content
            platform: Target platform (facebook, instagram, twitter, linkedin, youtube, tiktok)
            current_format: Current format if converting
        
        Returns:
            Dict with optimized content and recommendations
        """
        try:
            client = AIService._get_client()
            
            platform_requirements = {
                "facebook": "280-500 characters, engaging, shareable",
                "instagram": "2200 characters max, visual-first, hashtags important",
                "twitter": "280 characters max, concise, trending topics",
                "linkedin": "Professional tone, 1300 characters max, industry-focused",
                "youtube": "Long-form, detailed, SEO-optimized descriptions",
                "tiktok": "Short, punchy, trending, hook-driven"
            }
            
            requirements = platform_requirements.get(platform.lower(), "platform-appropriate")
            
            prompt = f"""Optimize this content for {platform}:

Original content:
{content}

Current format: {current_format or 'general'}

Platform requirements: {requirements}

Provide:
1. Optimized content
2. Platform-specific recommendations
3. Best posting times (if applicable)
4. Engagement tips

Format as JSON with: optimized_content, recommendations, best_practices
"""
            
            # Use gemini-3-pro-preview for content optimization
            response = client.models.generate_content(
                model="gemini-3-pro-preview",
                contents=prompt,
            )
            content_result = response.text
            
            try:
                result = json.loads(content_result)
            except json.JSONDecodeError:
                result = {
                    "optimized_content": content[:280] if platform == "twitter" else content,
                    "recommendations": [],
                    "best_practices": []
                }
            
            return {
                "success": True,
                "original_content": content,
                "optimized_content": result.get("optimized_content", content),
                "recommendations": result.get("recommendations", []),
                "best_practices": result.get("best_practices", []),
                "platform": platform,
                "character_count": len(result.get("optimized_content", content))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "optimized_content": content
            }
