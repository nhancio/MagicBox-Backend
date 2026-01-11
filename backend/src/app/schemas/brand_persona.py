"""
Brand Persona schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class BrandPersonaCreate(BaseModel):
    project_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tone: Optional[str] = None
    style: Optional[str] = None
    keywords: Optional[List[str]] = None
    avoid_keywords: Optional[List[str]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    is_default: bool = False


class BrandPersonaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tone: Optional[str] = None
    style: Optional[str] = None
    keywords: Optional[List[str]] = None
    avoid_keywords: Optional[List[str]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    is_default: Optional[bool] = None


class BrandPersonaRead(BaseModel):
    id: str
    project_id: str
    tenant_id: str
    name: str
    description: Optional[str]
    tone: Optional[str]
    style: Optional[str]
    keywords: Optional[List[str]]
    avoid_keywords: Optional[List[str]]
    examples: Optional[List[Dict[str, Any]]]
    is_default: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True
