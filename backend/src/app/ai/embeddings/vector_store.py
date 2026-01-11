"""
Vector Store - Interface for vector similarity search using embeddings.
Wraps EmbeddingService search functionality.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.embedding_service import EmbeddingService
from app.db.models.embedding import EmbeddingSource


class VectorStore:
    """Vector store for similarity search."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search(
        self,
        query: str,
        source_type: Optional[EmbeddingSource] = None,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content.
        
        Args:
            query: Search query text
            source_type: Optional filter by source type
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            List of similar items with similarity scores
        """
        return EmbeddingService.search_similar(
            db=self.db,
            query_text=query,
            source_type=source_type,
            limit=limit,
            threshold=threshold,
        )
    
    def search_artifacts(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for similar artifacts."""
        return self.search(
            query=query,
            source_type=EmbeddingSource.ARTIFACT,
            limit=limit,
            threshold=threshold,
        )
    
    def search_conversations(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """Search for similar conversation messages."""
        return self.search(
            query=query,
            source_type=EmbeddingSource.CONVERSATION,
            limit=limit,
            threshold=threshold,
        )
