"""
Conversation Repository - Data access layer for Conversation operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.conversation import Conversation, ConversationMessage


class ConversationRepository:
    """Repository for Conversation operations."""
    
    @staticmethod
    def get_by_id(db: Session, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    @staticmethod
    def get_by_tenant(db: Session, tenant_id: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get conversations by tenant."""
        return db.query(Conversation).filter(
            Conversation.tenant_id == tenant_id
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_messages(db: Session, conversation_id: str, skip: int = 0, limit: int = 100) -> List[ConversationMessage]:
        """Get messages for conversation."""
        return db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def create(db: Session, conversation: Conversation) -> Conversation:
        """Create conversation."""
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    
    @staticmethod
    def add_message(db: Session, message: ConversationMessage) -> ConversationMessage:
        """Add message to conversation."""
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
