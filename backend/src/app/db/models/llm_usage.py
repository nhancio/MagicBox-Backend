"""
LLM Usage Record model - tracks token usage and costs for billing and quota enforcement.
Source of truth for usage tracking (Langfuse is for observability).
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Float, Enum, JSON
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class UsageType(str, enum.Enum):
    COMPLETION = "COMPLETION"
    EMBEDDING = "EMBEDDING"
    IMAGE_GENERATION = "IMAGE_GENERATION"
    VIDEO_GENERATION = "VIDEO_GENERATION"


class LLMUsageRecord(Base):
    __tablename__ = "llm_usage_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)
    
    # Run reference
    run_id = Column(String, ForeignKey("runs.id"), nullable=True, index=True)
    
    # Usage type
    usage_type = Column(Enum(UsageType), nullable=False, index=True)
    
    # Model information
    provider = Column(String, nullable=False)  # e.g., "openai", "anthropic", "stability"
    model_name = Column(String, nullable=False)  # e.g., "gpt-4", "claude-3-opus"
    model_version = Column(String, nullable=True)
    
    # Token usage
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # Cost tracking
    cost_usd = Column(Float, nullable=True)  # Calculated cost in USD
    cost_per_1k_input = Column(Float, nullable=True)  # Rate for input tokens
    cost_per_1k_output = Column(Float, nullable=True)  # Rate for output tokens
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Date for aggregation (YYYY-MM-DD)
    usage_date = Column(DateTime, nullable=False, index=True)  # Date of usage for daily aggregation

