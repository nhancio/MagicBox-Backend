"""
Prompt Registry - Centralized prompt templates and management.
"""
from typing import Dict, Any, Optional
from enum import Enum


class PromptType(str, Enum):
    """Prompt types."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class PromptRegistry:
    """Registry for prompt templates."""
    
    _prompts: Dict[str, str] = {
        "post_generation": """Generate a {tone} social media post about: {topic}

Requirements:
- Platform: {platform}
- Target audience: {target_audience}
- Include hashtags: {hashtags}

Generate engaging, platform-appropriate content.""",
        
        "reel_generation": """Create a {duration_seconds}-second {style} video script about: {topic}

Requirements:
- Duration: {duration_seconds} seconds
- Opening hook: {hook}
- Style: {style}
- Include visual cues and scene descriptions""",
        
        "image_generation": """Create an image description for: {prompt}

Style: {style}
Dimensions: {dimensions}""",
    }
    
    @classmethod
    def get_prompt(cls, prompt_name: str, **kwargs) -> str:
        """Get a prompt template and format it with variables."""
        template = cls._prompts.get(prompt_name)
        if not template:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable for prompt '{prompt_name}': {e}")
    
    @classmethod
    def register_prompt(cls, name: str, template: str):
        """Register a new prompt template."""
        cls._prompts[name] = template
    
    @classmethod
    def list_prompts(cls) -> Dict[str, str]:
        """List all registered prompts."""
        return cls._prompts.copy()
