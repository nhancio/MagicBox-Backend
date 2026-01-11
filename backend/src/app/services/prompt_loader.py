"""
Prompt Loader - Loads system prompts from JSON files for agents.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class PromptLoader:
    """Loads and manages agent prompts from JSON files."""
    
    PROMPTS_DIR = Path(__file__).parent.parent / "ai" / "agents" / "prompts"
    
    _cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def load_prompt(cls, agent_name: str) -> Dict[str, Any]:
        """
        Load prompt configuration for an agent.
        
        Args:
            agent_name: Name of the agent (e.g., "post_agent", "reel_agent")
            
        Returns:
            Dict with system_prompt, version, model, temperature, max_tokens
        """
        # Check cache first
        if agent_name in cls._cache:
            return cls._cache[agent_name]
        
        # Construct filename
        prompt_file = cls.PROMPTS_DIR / f"{agent_name}_prompt.json"
        
        if not prompt_file.exists():
            # Return default prompt if file doesn't exist
            default_prompt = {
                "system_prompt": f"You are an AI assistant specialized in {agent_name.replace('_', ' ')} tasks. Provide helpful, accurate, and engaging responses.",
                "version": "1.0.0",
                "model": "gemini-pro",
                "temperature": 0.7,
                "max_tokens": 2000,
            }
            cls._cache[agent_name] = default_prompt
            return default_prompt
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_data = json.load(f)
                cls._cache[agent_name] = prompt_data
                return prompt_data
        except Exception as e:
            print(f"Warning: Failed to load prompt for {agent_name}: {e}")
            # Return default
            default_prompt = {
                "system_prompt": f"You are an AI assistant specialized in {agent_name.replace('_', ' ')} tasks.",
                "version": "1.0.0",
                "model": "gemini-pro",
                "temperature": 0.7,
                "max_tokens": 2000,
            }
            cls._cache[agent_name] = default_prompt
            return default_prompt
    
    @classmethod
    def get_system_prompt(cls, agent_name: str) -> str:
        """Get just the system prompt text."""
        prompt_data = cls.load_prompt(agent_name)
        return prompt_data.get("system_prompt", "")
    
    @classmethod
    def get_prompt_config(cls, agent_name: str) -> Dict[str, Any]:
        """Get prompt configuration (model, temperature, etc.)."""
        prompt_data = cls.load_prompt(agent_name)
        return {
            "model": prompt_data.get("model", "gemini-pro"),
            "temperature": prompt_data.get("temperature", 0.7),
            "max_tokens": prompt_data.get("max_tokens", 2000),
        }
    
    @classmethod
    def reload_cache(cls):
        """Reload all prompts from files (useful for development)."""
        cls._cache.clear()
