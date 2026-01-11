"""
Run schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.db.models.run import RunStatus


class RunCreate(BaseModel):
    agent_id: str
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    input_context: Optional[Dict[str, Any]] = None
    prompt_version_id: Optional[str] = None
    model_name: Optional[str] = None


class RunUpdate(BaseModel):
    status: Optional[RunStatus] = None
    error_message: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    artifact_id: Optional[str] = None


class RunRead(BaseModel):
    id: str
    tenant_id: str
    project_id: Optional[str]
    conversation_id: Optional[str]
    user_id: str
    agent_id: str
    agent_name: str
    status: RunStatus
    error_message: Optional[str]
    retry_count: int
    parent_run_id: Optional[str]
    input_context: Optional[Dict[str, Any]]
    prompt_version_id: Optional[str]
    model_name: Optional[str]
    model_version: Optional[str]
    provider: Optional[str]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    total_tokens: Optional[int]
    cost_usd: Optional[float]
    artifact_id: Optional[str]
    output_data: Optional[Dict[str, Any]]
    langfuse_trace_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
