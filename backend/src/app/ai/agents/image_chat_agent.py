"""
Image Chat Agent - Conversational agent for image generation.
Handles natural language requests and generates marketing images.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.db.models.agent import Agent
from app.ai.agents.conversational_agent import ConversationalAgent
from app.services.ai_service import AIService
from app.services.ai_image_service import AIImageService
from app.db.models.artifact import ArtifactType
import json
import re


class ImageChatAgent(ConversationalAgent):
    """Conversational agent for generating marketing images."""
    
    def _generate_conversational_response(
        self,
        user_message: str,
        context: str,
        attachments: Optional[List[Dict[str, Any]]],
        run_id: str,
    ) -> Dict[str, Any]:
        """
        Generate conversational response and create image.
        
        Handles natural language requests like:
        - "Create an image for my coffee shop promotion"
        - "Make a social media post image about our new product"
        - "Generate a banner for Instagram"
        """
        # Parse user intent from message
        intent = self._parse_image_intent(user_message)
        
        # Generate helpful response explaining what we'll create
        system_prompt = self.get_system_prompt()
        
        # Build prompt for image generation
        image_prompt = self._build_image_prompt(user_message, intent)
        
        # Generate image
        image_result = AIImageService.generate_image(
            prompt=image_prompt,
            output_path=None,  # Will be stored in artifact
        )
        
        if not image_result.get("success"):
            return {
                "response": f"I apologize, but I encountered an error generating the image: {image_result.get('error', 'Unknown error')}. Could you please try rephrasing your request?",
                "metadata": {"error": image_result.get("error")},
            }
        
        # Create conversational response
        response_text = self._create_response_text(intent, image_result)
        
        # Prepare artifact data
        artifact_data = {
            "type": "IMAGE",
            "title": intent.get("title", "Generated Marketing Image"),
            "content": None,
            "content_data": {
                "prompt": image_prompt,
                "intent": intent,
                "style": intent.get("style"),
                "platform": intent.get("platform"),
            },
            "image_url": image_result.get("image_path"),
            "prompt_used": image_prompt,
        }
        
        return {
            "response": response_text,
            "artifact_data": artifact_data,
            "metadata": {
                "image_path": image_result.get("image_path"),
                "prompt": image_prompt,
                "intent": intent,
            },
        }
    
    def _parse_image_intent(self, message: str) -> Dict[str, Any]:
        """Parse user message to extract image generation intent."""
        message_lower = message.lower()
        
        intent = {
            "type": "marketing_image",
            "platform": None,
            "style": None,
            "purpose": None,
            "title": None,
        }
        
        # Detect platform
        if "instagram" in message_lower or "ig" in message_lower:
            intent["platform"] = "instagram"
        elif "facebook" in message_lower or "fb" in message_lower:
            intent["platform"] = "facebook"
        elif "twitter" in message_lower or "x" in message_lower:
            intent["platform"] = "twitter"
        elif "linkedin" in message_lower:
            intent["platform"] = "linkedin"
        elif "tiktok" in message_lower:
            intent["platform"] = "tiktok"
        
        # Detect style
        if "vibrant" in message_lower or "colorful" in message_lower:
            intent["style"] = "vibrant"
        elif "minimal" in message_lower or "clean" in message_lower:
            intent["style"] = "minimal"
        elif "professional" in message_lower or "corporate" in message_lower:
            intent["style"] = "professional"
        elif "fun" in message_lower or "playful" in message_lower:
            intent["style"] = "fun"
        
        # Detect purpose
        if "promotion" in message_lower or "promo" in message_lower:
            intent["purpose"] = "promotion"
        elif "product" in message_lower:
            intent["purpose"] = "product"
        elif "banner" in message_lower:
            intent["purpose"] = "banner"
        elif "post" in message_lower:
            intent["purpose"] = "post"
        elif "ad" in message_lower or "advertisement" in message_lower:
            intent["purpose"] = "advertisement"
        
        # Extract title from message
        # Try to find quoted text or key phrases
        title_match = re.search(r'["\']([^"\']+)["\']', message)
        if title_match:
            intent["title"] = title_match.group(1)
        else:
            # Use first part of message as title
            words = message.split()[:5]
            intent["title"] = " ".join(words)
        
        return intent
    
    def _build_image_prompt(self, user_message: str, intent: Dict[str, Any]) -> str:
        """Build detailed image generation prompt from user message and intent."""
        # Start with user's message
        prompt_parts = [user_message]
        
        # Add style guidance
        if intent.get("style"):
            prompt_parts.append(f"Style: {intent['style']}")
        
        # Add platform-specific requirements
        if intent.get("platform"):
            platform_requirements = {
                "instagram": "Square format, vibrant colors, engaging composition",
                "facebook": "Rectangular format, clear messaging, professional",
                "twitter": "Horizontal format, bold text, eye-catching",
                "linkedin": "Professional, clean design, business-focused",
                "tiktok": "Vertical format, dynamic, trendy",
            }
            if intent["platform"] in platform_requirements:
                prompt_parts.append(platform_requirements[intent["platform"]])
        
        # Add marketing context
        if intent.get("purpose"):
            prompt_parts.append(f"Purpose: Marketing {intent['purpose']} for small business")
        
        # Enhance with marketing best practices
        prompt_parts.append("High quality, professional marketing image suitable for social media")
        prompt_parts.append("Clear, readable text if text is included")
        prompt_parts.append("Eye-catching and engaging design")
        
        return ", ".join(prompt_parts)
    
    def _create_response_text(self, intent: Dict[str, Any], image_result: Dict[str, Any]) -> str:
        """Create natural language response about the generated image."""
        platform_text = f" for {intent['platform'].title()}" if intent.get("platform") else ""
        style_text = f" with a {intent['style']} style" if intent.get("style") else ""
        
        response = f"I've created a marketing image{platform_text}{style_text} for you! "
        
        if intent.get("purpose"):
            response += f"This {intent['purpose']} image is ready to use. "
        
        response += "You can download it, schedule it for posting, or ask me to make any adjustments you'd like."
        
        return response
