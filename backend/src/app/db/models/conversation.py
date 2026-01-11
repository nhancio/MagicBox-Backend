"""
Conversation model - represents a chat session with the AI.
Supports retention policies and message history.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Boolean, Integer
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime, timedelta
import uuid


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    title = Column(String, nullable=True)  # Auto-generated or user-set
    context = Column(Text, nullable=True)  # Conversation context/summary
    
    # Retention policy
    retention_days = Column(Integer, default=90, nullable=False)  # Default 90 days
    expires_at = Column(DateTime, nullable=True)  # Calculated from retention_days
    
    # Metadata
    is_archived = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_message_at = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="conversations", lazy="select")
    # messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.retention_days and not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=self.retention_days)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Null for AI messages
    
    role = Column(String, nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    
    # AI metadata (for assistant messages)
    run_id = Column(String, ForeignKey("runs.id"), nullable=True)  # Link to AI run
    model_used = Column(String, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    # conversation = relationship("Conversation", back_populates="messages")

