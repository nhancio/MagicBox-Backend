#!/usr/bin/env python3
"""Fix run.py file encoding"""
content = '''"""
Run model - represents one execution of an agent.
Tracks the full lifecycle: PENDING → RUNNING → SUCCESS/FAILED → RETRIED
Stores input context, prompt version, model version, token usage, output references.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Enum, JSON, Integer, Float
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class RunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    RETRIED = "RETRIED"
    CANCELLED = "CANCELLED"


class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Agent reference
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    agent_name = Column(String, nullable=False)  # Denormalized for quick access
    
    # Status and lifecycle
    status = Column(Enum(RunStatus), default=RunStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    parent_run_id = Column(String, ForeignKey("runs.id"), nullable=True)  # For retries
    
    # Input context
    input_context = Column(JSON, nullable=True)  # User input and context
    prompt_version_id = Column(String, ForeignKey("prompt_versions.id"), nullable=True)
    
    # Model information
    model_name = Column(String, nullable=True)  # e.g., "gpt-4", "claude-3"
    model_version = Column(String, nullable=True)
    provider = Column(String, nullable=True)  # e.g., "openai", "anthropic"
    
    # Token usage
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)  # Estimated cost
    
    # Output references
    artifact_id = Column(String, ForeignKey("artifacts.id"), nullable=True)  # Generated artifact
    output_data = Column(JSON, nullable=True)  # Raw output data
    
    # Observability
    langfuse_trace_id = Column(String, nullable=True)  # Link to Langfuse trace
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    # artifact = relationship("Artifact", back_populates="run")
    # prompt_version = relationship("PromptVersion", back_populates="runs")
'''

with open('src/app/db/models/run.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed run.py")
