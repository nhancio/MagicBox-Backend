"""
Project schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    brand_guidelines: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    brand_voice: Optional[str] = None
    target_audience: Optional[str] = None
    brand_guidelines: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectRead(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    brand_voice: Optional[str]
    target_audience: Optional[str]
    brand_guidelines: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True
