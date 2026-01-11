"""
Chat-based Content Generation Service - Conversational AI for content creation.
Enables natural language requests like "I need a reel which promotes my brand..."
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import re

from app.services.ai_service import AIService
from app.services.content_service import ContentService
from app.db.models.conversation import Conversation, ConversationMessage
from app.db.models.artifact import Artifact, ArtifactType, ArtifactStatus
from app.db.models.social_account import SocialPlatform
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID


class ChatContentService:
    """Service for conversational content generation."""
    
    @staticmethod
    def process_content_request(
        db: Session,
        conversation_id: str,
        user_message: str,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a user's natural language content request.
        Analyzes the request and generates appropriate content.
        
        Examples:
        - "I need a reel which promotes my brand truvelocity"
        - "Create an Instagram story for my product launch"
        - "Generate a post about 5 marketing tips"
        """
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id or not user_id:
            raise ValueError("Tenant ID and User ID must be in request context")
        
        # Get conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.tenant_id == tenant_id
        ).first()
        
        if not conversation:
            raise ValueError("Conversation not found")
        
        # Save user message
        from app.db.models.conversation import ConversationMessage
        user_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content=user_message,
        )
        db.add(user_msg)
        db.commit()
        
        # Analyze request using AI
        content_type, platform, details = ChatContentService._analyze_request(user_message)
        
        # Generate AI response
        ai_response = ChatContentService._generate_ai_response(content_type, platform, details)
        
        # Save AI response
        from app.db.models.conversation import ConversationMessage
        ai_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=None,  # AI messages have no user_id
            role="assistant",
            content=ai_response["message"],
        )
        db.add(ai_msg)
        
        # Generate content if request is clear
        artifact = None
        if content_type and details.get("topic"):
            try:
                artifact = ChatContentService._generate_content(
                    db=db,
                    content_type=content_type,
                    platform=platform,
                    details=details,
                    project_id=project_id or conversation.project_id,
                )
                
                # Store artifact reference in message (we'll need to add a JSON field or use a separate table)
                # For now, we'll store it in the conversation context
                pass
            except Exception as e:
                # Log error but don't fail the conversation
                pass
        
        # Update conversation
        conversation.last_message_at = datetime.utcnow()
        if not conversation.title:
            # Auto-generate title from first message
            conversation.title = user_message[:50] + "..." if len(user_message) > 50 else user_message
        
        db.commit()
        db.refresh(ai_msg)
        
        return {
            "conversation_id": conversation_id,
            "user_message": user_message,
            "ai_response": ai_response["message"],
            "artifact": {
                "id": artifact.id,
                "type": artifact.type.value,
                "content": artifact.content[:200] + "..." if artifact.content and len(artifact.content) > 200 else artifact.content,
                "status": artifact.status.value,
            } if artifact else None,
            "content_type": content_type,
            "platform": platform.value if platform else None,
        }
    
    @staticmethod
    def _analyze_request(message: str) -> tuple[Optional[str], Optional[SocialPlatform], Dict[str, Any]]:
        """
        Analyze user message to extract:
        - Content type (post, reel, story, video, etc.)
        - Platform (instagram, facebook, etc.)
        - Details (topic, tone, etc.)
        """
        message_lower = message.lower()
        
        # Detect content type
        content_type = None
        if any(word in message_lower for word in ["reel", "reels", "short", "shorts"]):
            content_type = "reel"
        elif any(word in message_lower for word in ["story", "stories", "instagram story"]):
            content_type = "story"
        elif any(word in message_lower for word in ["video", "youtube", "long-form"]):
            content_type = "video"
        elif any(word in message_lower for word in ["post", "posts", "content"]):
            content_type = "post"
        
        # Detect platform
        platform = None
        if "instagram" in message_lower or "ig" in message_lower:
            platform = SocialPlatform.INSTAGRAM
        elif "facebook" in message_lower or "fb" in message_lower:
            platform = SocialPlatform.FACEBOOK
        elif "twitter" in message_lower or "x" in message_lower:
            platform = SocialPlatform.TWITTER
        elif "linkedin" in message_lower:
            platform = SocialPlatform.LINKEDIN
        elif "youtube" in message_lower or "yt" in message_lower:
            platform = SocialPlatform.YOUTUBE
        elif "tiktok" in message_lower:
            platform = SocialPlatform.TIKTOK
        
        # Extract topic/brand name
        topic = None
        # Look for patterns like "promotes my brand X" or "about X"
        brand_match = re.search(r'(?:brand|product|company|about|for)\s+([A-Za-z0-9\s]+?)(?:\s|$|\.|,|!|\?)', message, re.IGNORECASE)
        if brand_match:
            topic = brand_match.group(1).strip()
        else:
            # Fallback: use first sentence or key phrases
            sentences = message.split('.')
            if sentences:
                topic = sentences[0].strip()
        
        # Extract tone/style
        tone = "professional"
        if any(word in message_lower for word in ["casual", "friendly", "fun"]):
            tone = "casual"
        elif any(word in message_lower for word in ["professional", "business", "corporate"]):
            tone = "professional"
        elif any(word in message_lower for word in ["creative", "artistic", "bold"]):
            tone = "creative"
        
        return content_type, platform, {
            "topic": topic or "marketing content",
            "tone": tone,
            "original_message": message,
        }
    
    @staticmethod
    def _generate_ai_response(content_type: Optional[str], platform: Optional[SocialPlatform], details: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a friendly AI response message."""
        if content_type == "reel":
            message = f"Awesome! Generating your {platform.value if platform else 'Instagram'} Reel now. Hang tight!"
        elif content_type == "story":
            message = f"Awesome! Generating your Instagram Story now. Hang tight!"
        elif content_type == "video":
            message = f"Great! Creating your video script now. This might take a moment..."
        elif content_type == "post":
            message = f"Perfect! Generating your {platform.value if platform else 'social media'} post now. Hang tight!"
        else:
            message = "I'll help you create that content! Generating now..."
        
        return {"message": message}
    
    @staticmethod
    def _generate_content(
        db: Session,
        content_type: str,
        platform: Optional[SocialPlatform],
        details: Dict[str, Any],
        project_id: Optional[str],
    ) -> Artifact:
        """Generate the actual content based on type."""
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if content_type == "reel":
            result = ContentService.generate_reel_script(
                db=db,
                topic=details["topic"],
                duration_seconds=30,
                style=details.get("tone", "engaging"),
                project_id=project_id,
            )
            return result["artifact"]
        
        elif content_type == "story":
            # Stories are similar to posts but optimized for Instagram Stories
            result = ContentService.generate_and_create_post(
                db=db,
                topic=details["topic"],
                platform=platform or SocialPlatform.INSTAGRAM,
                tone=details.get("tone", "professional"),
                project_id=project_id,
            )
            return result["artifact"]
        
        elif content_type == "video":
            result = ContentService.generate_video_script(
                db=db,
                topic=details["topic"],
                duration_minutes=5,
                format="tutorial",
                project_id=project_id,
            )
            return result["artifact"]
        
        else:  # post or default
            result = ContentService.generate_and_create_post(
                db=db,
                topic=details["topic"],
                platform=platform or SocialPlatform.FACEBOOK,
                tone=details.get("tone", "professional"),
                project_id=project_id,
            )
            return result["artifact"]
