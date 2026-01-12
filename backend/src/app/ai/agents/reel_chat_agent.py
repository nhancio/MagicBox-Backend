"""
Reel Chat Agent - Conversational agent for reel/shorts generation.
Handles natural language requests and generates video scripts and content.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.db.models.agent import Agent
from app.ai.agents.conversational_agent import ConversationalAgent
from app.services.ai_service import AIService
from app.services.ai_video_service import AIVideoService
from app.db.models.artifact import ArtifactType
import json
import re


class ReelChatAgent(ConversationalAgent):
    """Conversational agent for generating reels and shorts."""
    
    def _generate_conversational_response(
        self,
        user_message: str,
        context: str,
        attachments: Optional[List[Dict[str, Any]]],
        run_id: str,
    ) -> Dict[str, Any]:
        """
        Generate conversational response and create reel script/video.
        
        Handles natural language requests like:
        - "Create a reel for my product launch"
        - "Make a short video about our new service"
        - "Generate a TikTok video script"
        """
        # Parse user intent
        intent = self._parse_reel_intent(user_message)
        
        # Generate reel script
        script_result = AIService.generate_reel_script(
            topic=user_message,
            duration_seconds=intent.get("duration", 30),
            style=intent.get("style", "engaging"),
            hook=intent.get("hook"),
        )
        
        if not script_result.get("success"):
            return {
                "response": f"I apologize, but I encountered an error generating the reel script: {script_result.get('error', 'Unknown error')}. Could you please try rephrasing your request?",
                "metadata": {"error": script_result.get("error")},
            }
        
        # Optionally generate video (if user explicitly asks)
        video_result = None
        if intent.get("generate_video", False):
            video_prompt = f"{script_result.get('hook', '')} {script_result.get('script', '')}"
            
            # Prepare script data for scene planning
            script_data = {
                "hook": script_result.get("hook", ""),
                "script": script_result.get("script", ""),
                "scenes": script_result.get("scenes", []),
                "call_to_action": script_result.get("call_to_action", ""),
            }
            
            video_result = AIVideoService.generate_video(
                prompt=video_prompt,
                output_path=None,
                duration_seconds=intent.get("duration", 30),
                script_data=script_data,  # Pass script data for better scene planning
            )
        
        # Create conversational response
        response_text = self._create_response_text(intent, script_result, video_result)
        
        # Prepare artifact data
        artifact_data = {
            "type": "REEL" if not video_result else "VIDEO",
            "title": intent.get("title", "Generated Reel Script"),
            "content": script_result.get("script"),
            "content_data": {
                "script": script_result.get("script"),
                "hook": script_result.get("hook"),
                "scenes": script_result.get("scenes", []),
                "call_to_action": script_result.get("call_to_action"),
                "duration_seconds": intent.get("duration", 30),
                "platform": intent.get("platform"),
            },
            "video_url": video_result.get("video_path") if video_result and video_result.get("success") else None,
            "prompt_used": user_message,
        }
        
        return {
            "response": response_text,
            "artifact_data": artifact_data,
            "metadata": {
                "script": script_result,
                "video": video_result if video_result else None,
                "intent": intent,
            },
        }
    
    def _parse_reel_intent(self, message: str) -> Dict[str, Any]:
        """Parse user message to extract reel generation intent."""
        message_lower = message.lower()
        
        intent = {
            "type": "reel",
            "platform": None,
            "style": None,
            "duration": 30,
            "generate_video": False,
            "hook": None,
            "title": None,
        }
        
        # Detect platform
        if "reel" in message_lower or "instagram" in message_lower:
            intent["platform"] = "instagram_reels"
        elif "tiktok" in message_lower:
            intent["platform"] = "tiktok"
        elif "short" in message_lower or "youtube" in message_lower:
            intent["platform"] = "youtube_shorts"
        elif "short" in message_lower:
            intent["platform"] = "shorts"
        
        # Detect duration
        duration_match = re.search(r'(\d+)\s*(?:second|sec|s)', message_lower)
        if duration_match:
            intent["duration"] = int(duration_match.group(1))
        elif "short" in message_lower:
            intent["duration"] = 15
        elif "long" in message_lower:
            intent["duration"] = 60
        
        # Detect style
        if "engaging" in message_lower or "viral" in message_lower:
            intent["style"] = "engaging"
        elif "funny" in message_lower or "humor" in message_lower:
            intent["style"] = "funny"
        elif "educational" in message_lower or "tutorial" in message_lower:
            intent["style"] = "educational"
        elif "trendy" in message_lower or "trending" in message_lower:
            intent["style"] = "trendy"
        
        # Detect if video generation is requested
        if "video" in message_lower or "generate video" in message_lower or "create video" in message_lower:
            intent["generate_video"] = True
        
        # Extract hook if mentioned
        hook_match = re.search(r'hook[:\s]+["\']?([^"\']+)["\']?', message_lower)
        if hook_match:
            intent["hook"] = hook_match.group(1)
        
        # Extract title
        title_match = re.search(r'["\']([^"\']+)["\']', message)
        if title_match:
            intent["title"] = title_match.group(1)
        else:
            words = message.split()[:5]
            intent["title"] = " ".join(words)
        
        return intent
    
    def _create_response_text(
        self,
        intent: Dict[str, Any],
        script_result: Dict[str, Any],
        video_result: Optional[Dict[str, Any]],
    ) -> str:
        """Create natural language response about the generated reel."""
        platform_text = ""
        if intent.get("platform"):
            platform_names = {
                "instagram_reels": "Instagram Reel",
                "tiktok": "TikTok video",
                "youtube_shorts": "YouTube Short",
                "shorts": "short video",
            }
            platform_text = f" {platform_names.get(intent['platform'], 'reel')}"
        
        response = f"I've created a{platform_text} script for you! "
        
        if script_result.get("hook"):
            response += f"The hook is: '{script_result['hook']}'. "
        
        response += f"The script is {intent.get('duration', 30)} seconds long and includes engaging scenes. "
        
        if video_result and video_result.get("success"):
            response += "I've also generated the video for you! "
        else:
            response += "You can use this script to create your video, or ask me to generate the video for you. "
        
        response += "Would you like me to make any adjustments or schedule it for posting?"
        
        return response
