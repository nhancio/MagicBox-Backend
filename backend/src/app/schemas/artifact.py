"""
Artifact schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.db.models.artifact import ArtifactType, ArtifactStatus


class ArtifactCreate(BaseModel):
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    type: ArtifactType
    title: Optional[str] = None
    content: Optional[str] = None
    content_data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class ArtifactUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[ArtifactStatus] = None
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class ArtifactRead(BaseModel):
    id: str
    tenant_id: str
    project_id: Optional[str]
    conversation_id: Optional[str]
    user_id: str
    run_id: Optional[str]
    type: ArtifactType
    status: ArtifactStatus
    version: int
    parent_artifact_id: Optional[str]
    title: Optional[str]
    content: Optional[str]
    content_data: Optional[Dict[str, Any]]
    image_url: Optional[str]
    video_url: Optional[str]
    thumbnail_url: Optional[str]
    extra_metadata: Optional[Dict[str, Any]]
    tags: Optional[List[str]]
    prompt_used: Optional[str]
    model_used: Optional[str]
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True
