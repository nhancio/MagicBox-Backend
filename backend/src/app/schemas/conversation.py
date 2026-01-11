"""
Conversation schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ConversationCreate(BaseModel):
    project_id: Optional[str] = None
    title: Optional[str] = None
    context: Optional[str] = None
    retention_days: int = Field(default=90, ge=1, le=365)


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    context: Optional[str] = None
    is_archived: Optional[bool] = None


class ConversationMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    role: str = Field(..., pattern="^(user|assistant|system)$")


class ConversationMessageRead(BaseModel):
    id: str
    conversation_id: str
    user_id: Optional[str]
    role: str
    content: str
    run_id: Optional[str]
    model_used: Optional[str]
    tokens_used: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationRead(BaseModel):
    id: str
    tenant_id: str
    project_id: Optional[str]
    user_id: str
    title: Optional[str]
    context: Optional[str]
    retention_days: int
    expires_at: Optional[datetime]
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationRead):
    messages: List[ConversationMessageRead] = []
