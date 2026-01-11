"""
Session Memory - Manages conversation context and short-term memory for AI agents.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models.conversation import Conversation, ConversationMessage
from app.services.conversation_service import ConversationService


class SessionMemory:
    """Manages session-level memory for conversations."""
    
    def __init__(self, db: Session, conversation_id: str):
        self.db = db
        self.conversation_id = conversation_id
        self._conversation: Optional[Conversation] = None
    
    @property
    def conversation(self) -> Conversation:
        """Get conversation object."""
        if self._conversation is None:
            self._conversation = ConversationService.get_conversation(self.db, self.conversation_id)
            if not self._conversation:
                raise ValueError(f"Conversation {self.conversation_id} not found")
        return self._conversation
    
    def get_messages(self, limit: int = 50) -> List[ConversationMessage]:
        """Get recent messages from the conversation."""
        return ConversationService.get_messages(
            self.db,
            self.conversation_id,
            skip=0,
            limit=limit
        )
    
    def get_context(self) -> str:
        """Get conversation context/summary."""
        return self.conversation.context or ""
    
    def update_context(self, context: str):
        """Update conversation context."""
        from app.services.conversation_service import ConversationService
        from app.schemas.conversation import ConversationUpdate
        
        ConversationService.update_conversation(
            self.db,
            self.conversation_id,
            ConversationUpdate(context=context)
        )
        self._conversation = None  # Invalidate cache
    
    def get_recent_history(self, last_n: int = 10) -> List[Dict[str, str]]:
        """Get recent message history as list of dicts."""
        messages = self.get_messages(limit=last_n)
        return [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in messages
        ]
    
    def add_to_memory(self, role: str, content: str):
        """Add a message to the conversation."""
        from app.schemas.conversation import ConversationMessageCreate
        
        ConversationService.add_message(
            self.db,
            self.conversation_id,
            ConversationMessageCreate(role=role, content=content)
        )
