"""
Long-term Memory - Manages persistent knowledge and embeddings for RAG.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.ai.embeddings.vector_store import VectorStore
from app.db.models.embedding import EmbeddingSource


class LongTermMemory:
    """Manages long-term memory using embeddings and vector search."""
    
    def __init__(self, db: Session):
        self.db = db
        self.vector_store = VectorStore(db)
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search long-term memory for relevant information."""
        return self.vector_store.search(
            query=query,
            limit=limit,
            threshold=0.7,
        )
    
    def search_artifacts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for relevant artifacts."""
        return self.vector_store.search_artifacts(query=query, limit=limit)
    
    def search_conversations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for relevant conversation history."""
        return self.vector_store.search_conversations(query=query, limit=limit)
    
    def get_relevant_context(
        self,
        query: str,
        source_types: Optional[List[EmbeddingSource]] = None,
        limit: int = 5,
    ) -> str:
        """
        Get relevant context from long-term memory as formatted string.
        
        Args:
            query: Search query
            source_types: Optional list of source types to search
            limit: Maximum number of results
            
        Returns:
            Formatted context string
        """
        if source_types:
            results = []
            for source_type in source_types:
                results.extend(
                    self.vector_store.search(
                        query=query,
                        source_type=source_type,
                        limit=limit,
                    )
                )
        else:
            results = self.search(query=query, limit=limit)
        
        if not results:
            return ""
        
        # Format results as context
        context_parts = []
        for result in results[:limit]:
            content = result.get("content", "")
            if content:
                context_parts.append(f"- {content[:200]}...")
        
        return "\n".join(context_parts)
