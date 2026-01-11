"""
AI Model model - registry of available AI models with configuration.
Supports model routing and fallback strategies.
"""
from sqlalchemy import Column, String, Text, DateTime, Boolean, JSON, Float, Integer
from app.db.base import Base
from datetime import datetime
import uuid


class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Model identification
    name = Column(String, nullable=False, unique=True)  # e.g., "gpt-4", "claude-3-opus"
    provider = Column(String, nullable=False)  # e.g., "openai", "anthropic"
    model_type = Column(String, nullable=False)  # e.g., "completion", "embedding", "image", "video"
    
    # Configuration
    description = Column(Text, nullable=True)
    max_tokens = Column(Integer, nullable=True)  # Max output tokens
    context_window = Column(Integer, nullable=True)  # Max input tokens
    
    # Pricing (per 1K tokens)
    cost_per_1k_input = Column(Float, nullable=True)
    cost_per_1k_output = Column(Float, nullable=True)
    
    # Model capabilities
    supports_streaming = Column(Boolean, default=False, nullable=False)
    supports_function_calling = Column(Boolean, default=False, nullable=False)
    supports_vision = Column(Boolean, default=False, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)  # Default for model_type
    
    # Configuration
    config = Column(JSON, nullable=True)  # Model-specific configuration
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

