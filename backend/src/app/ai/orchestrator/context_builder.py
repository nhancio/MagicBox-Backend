"""
Context Builder - Builds context for AI agents from various sources.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.ai.memory.session_memory import SessionMemory
from app.ai.memory.long_term_memory import LongTermMemory
from app.ai.memory.episodic_memory import EpisodicMemory


class ContextBuilder:
    """Builds context for AI operations."""
    
    def __init__(self, db: Session, conversation_id: Optional[str] = None, user_id: Optional[str] = None):
        self.db = db
        self.conversation_id = conversation_id
        self.user_id = user_id
        
        # Initialize memory systems
        if conversation_id:
            self.session_memory = SessionMemory(db, conversation_id)
        else:
            self.session_memory = None
        
        self.long_term_memory = LongTermMemory(db)
        
        if user_id:
            self.episodic_memory = EpisodicMemory(db, user_id=user_id)
        else:
            self.episodic_memory = None
    
    def build_context(
        self,
        query: Optional[str] = None,
        include_session: bool = True,
        include_long_term: bool = True,
        include_episodic: bool = True,
    ) -> str:
        """Build comprehensive context."""
        context_parts = []
        
        # Session context
        if include_session and self.session_memory:
            recent_history = self.session_memory.get_recent_history(last_n=5)
            if recent_history:
                context_parts.append("=== Recent Conversation ===")
                for msg in recent_history:
                    context_parts.append(f"{msg['role']}: {msg['content'][:200]}")
        
        # Long-term memory context
        if include_long_term and query:
            relevant_context = self.long_term_memory.get_relevant_context(query, limit=3)
            if relevant_context:
                context_parts.append("\n=== Relevant Context ===")
                context_parts.append(relevant_context)
        
        # Episodic memory (user preferences)
        if include_episodic and self.episodic_memory:
            preferences = self.episodic_memory.get_preferences()
            if preferences.get("preferred_content_types"):
                context_parts.append("\n=== User Preferences ===")
                context_parts.append(f"Preferred content types: {list(preferences['preferred_content_types'].keys())}")
        
        return "\n\n".join(context_parts)
