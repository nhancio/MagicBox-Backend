"""
Model Router - Routes requests to appropriate AI models based on configuration.
"""
from typing import Optional, Dict, Any
from app.config.settings import settings


class ModelRouter:
    """Routes requests to appropriate models."""
    
    DEFAULT_MODEL = "gemini-pro"
    
    @staticmethod
    def get_model_for_task(task_type: str, model_preference: Optional[str] = None) -> str:
        """
        Get appropriate model for a task.
        
        Args:
            task_type: Type of task (post, reel, image, etc.)
            model_preference: User-specified model preference
            
        Returns:
            Model name to use
        """
        if model_preference:
            return model_preference
        
        # Route based on task type
        model_map = {
            "post": "gemini-pro",
            "reel": "gemini-pro",
            "video": "gemini-pro",
            "image": "gemini-pro",  # Would use image generation model in production
            "embedding": "text-embedding-004",
        }
        
        return model_map.get(task_type.lower(), ModelRouter.DEFAULT_MODEL)
    
    @staticmethod
    def get_model_config(model_name: str) -> Dict[str, Any]:
        """Get configuration for a model."""
        # In production, this would fetch from database or config
        return {
            "name": model_name,
            "provider": "google" if "gemini" in model_name.lower() else "unknown",
            "max_tokens": 8192,
            "temperature": 0.7,
        }
