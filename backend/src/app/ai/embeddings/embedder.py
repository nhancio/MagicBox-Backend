"""
Embedder - Wrapper around EmbeddingService for AI module integration.
Provides a clean interface for generating embeddings.
"""
from typing import List, Optional
from app.services.embedding_service import EmbeddingService


class Embedder:
    """Wrapper for embedding generation."""
    
    @staticmethod
    def embed_text(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            task_type: Task type ("RETRIEVAL_DOCUMENT" or "RETRIEVAL_QUERY")
            
        Returns:
            Embedding vector
        """
        return EmbeddingService.generate_embedding(text, task_type=task_type)
    
    @staticmethod
    def embed_query(query: str) -> List[float]:
        """Generate embedding for a search query."""
        return EmbeddingService.generate_embedding(query, task_type="RETRIEVAL_QUERY")
    
    @staticmethod
    def embed_document(document: str) -> List[float]:
        """Generate embedding for a document."""
        return EmbeddingService.generate_embedding(document, task_type="RETRIEVAL_DOCUMENT")
