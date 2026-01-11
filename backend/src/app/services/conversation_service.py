"""
Conversation Service - manages chat sessions with AI.
Follows architecture: multi-tenant, retention policies, message history.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.db.models.conversation import Conversation, ConversationMessage
from app.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationMessageCreate
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID


class ConversationService:
    """Service for managing conversations and messages."""

    @staticmethod
    def create_conversation(db: Session, conversation_data: ConversationCreate) -> Conversation:
        """Create a new conversation."""
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id:
            raise ValueError("Tenant ID not found in context")
        if not user_id:
            raise ValueError("User ID not found in context")
        
        conversation = Conversation(
            tenant_id=tenant_id,
            project_id=conversation_data.project_id,
            user_id=user_id,
            title=conversation_data.title,
            context=conversation_data.context,
            retention_days=conversation_data.retention_days,
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def get_conversation(db: Session, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID (tenant-scoped)."""
        tenant_id = get_context(CTX_TENANT_ID)
        
        return db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.tenant_id == tenant_id
        ).first()

    @staticmethod
    def list_conversations(
        db: Session,
        project_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Conversation]:
        """List conversations for the current tenant."""
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        query = db.query(Conversation).filter(
            Conversation.tenant_id == tenant_id,
            Conversation.user_id == user_id,
            Conversation.is_archived == False
        )
        
        if project_id:
            query = query.filter(Conversation.project_id == project_id)
        
        return query.order_by(Conversation.last_message_at.desc().nullslast()).offset(skip).limit(limit).all()

    @staticmethod
    def update_conversation(
        db: Session,
        conversation_id: str,
        conversation_data: ConversationUpdate
    ) -> Optional[Conversation]:
        """Update a conversation."""
        conversation = ConversationService.get_conversation(db, conversation_id)
        if not conversation:
            return None
        
        update_data = conversation_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversation, field, value)
        
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def add_message(
        db: Session,
        conversation_id: str,
        message_data: ConversationMessageCreate
    ) -> ConversationMessage:
        """Add a message to a conversation."""
        conversation = ConversationService.get_conversation(db, conversation_id)
        if not conversation:
            raise ValueError("Conversation not found")
        
        user_id = get_context(CTX_USER_ID)
        
        message = ConversationMessage(
            conversation_id=conversation_id,
            user_id=user_id if message_data.role == "user" else None,
            role=message_data.role,
            content=message_data.content,
        )
        
        # Update conversation's last_message_at
        conversation.last_message_at = datetime.utcnow()
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Create embedding for the message (async, non-blocking)
        try:
            from app.services.embedding_service import EmbeddingService
            # Only create embedding for user and assistant messages
            if message.role in ["user", "assistant"] and message.content:
                EmbeddingService.create_embedding_for_conversation_message(db, message.id)
        except Exception as e:
            # Don't fail message creation if embedding fails
            print(f"Warning: Failed to create embedding for message {message.id}: {e}")
        
        return message

    @staticmethod
    def get_messages(
        db: Session,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ConversationMessage]:
        """Get messages for a conversation."""
        # Verify conversation belongs to tenant
        conversation = ConversationService.get_conversation(db, conversation_id)
        if not conversation:
            return []
        
        return db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.created_at.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def archive_conversation(db: Session, conversation_id: str) -> bool:
        """Archive a conversation."""
        conversation = ConversationService.get_conversation(db, conversation_id)
        if not conversation:
            return False
        
        conversation.is_archived = True
        db.commit()
        return True

    @staticmethod
    def cleanup_expired_conversations(db: Session) -> int:
        """Clean up expired conversations based on retention policy."""
        tenant_id = get_context(CTX_TENANT_ID)
        now = datetime.utcnow()
        
        expired = db.query(Conversation).filter(
            Conversation.tenant_id == tenant_id,
            Conversation.expires_at <= now,
            Conversation.is_archived == False
        ).all()
        
        count = len(expired)
        for conversation in expired:
            conversation.is_archived = True
        
        db.commit()
        return count
