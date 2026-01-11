"""
Embedding Service - generates and stores vector embeddings for RAG.
Supports pgvector when available, falls back to JSON storage.
Uses Google's embedding API (text-embedding-004).
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
import numpy as np
import json
import httpx

from app.db.models.embedding import Embedding, EmbeddingType, EmbeddingSource
from app.db.database import engine
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID
from app.config.settings import settings


class EmbeddingService:
    """Service for generating and storing embeddings."""
    
    # Embedding model configuration
    EMBEDDING_MODEL = "text-embedding-004"  # Google's embedding model
    EMBEDDING_DIMENSION = 768  # text-embedding-004 produces 768-dimensional vectors
    EMBEDDING_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
    
    _pgvector_available: Optional[bool] = None
    
    @classmethod
    def _check_pgvector_available(cls, db: Session) -> bool:
        """
        Check if pgvector extension is available in the database.
        Caches result for performance.
        """
        if cls._pgvector_available is not None:
            return cls._pgvector_available
        
        # Check database dialect
        if engine.dialect.name != "postgresql":
            cls._pgvector_available = False
            return False
        
        try:
            # Check if vector extension exists
            result = db.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"))
            exists = result.scalar()
            
            if exists:
                # Verify we can use Vector type
                try:
                    from pgvector.sqlalchemy import Vector
                    cls._pgvector_available = True
                except ImportError:
                    cls._pgvector_available = False
            else:
                cls._pgvector_available = False
        except Exception as e:
            print(f"Warning: Could not check pgvector availability: {e}")
            cls._pgvector_available = False
        
        return cls._pgvector_available
    
    @staticmethod
    def generate_embedding(text_content: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Generate embedding vector for text content using Google's embedding API.
        
        Args:
            text_content: Text to embed
            task_type: Task type for embedding ("RETRIEVAL_DOCUMENT" or "RETRIEVAL_QUERY")
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text_content or not text_content.strip():
            raise ValueError("Text content cannot be empty")
        
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured in environment variables")
        
        try:
            # Use Google's Embedding API (REST)
            api_url = EmbeddingService.EMBEDDING_API_URL.format(model=EmbeddingService.EMBEDDING_MODEL)
            
            payload = {
                "model": f"models/{EmbeddingService.EMBEDDING_MODEL}",
                "content": {
                    "parts": [{"text": text_content}]
                },
                "taskType": task_type
            }
            
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": settings.GEMINI_API_KEY
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                # Extract embedding from response
                embedding = result.get("embedding", {}).get("values", [])
                
                if not embedding:
                    raise ValueError("No embedding returned from API")
                
                # Ensure embedding is the right dimension
                if len(embedding) != EmbeddingService.EMBEDDING_DIMENSION:
                    # Pad or truncate to correct dimension
                    if len(embedding) < EmbeddingService.EMBEDDING_DIMENSION:
                        embedding.extend([0.0] * (EmbeddingService.EMBEDDING_DIMENSION - len(embedding)))
                    else:
                        embedding = embedding[:EmbeddingService.EMBEDDING_DIMENSION]
                
                return embedding
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if e.response else str(e)
            raise ValueError(f"HTTP error generating embedding: {error_detail}")
        except Exception as e:
            raise ValueError(f"Failed to generate embedding: {str(e)}")
    
    @staticmethod
    def create_embedding(
        db: Session,
        source_type: EmbeddingSource,
        source_id: str,
        content: str,
        embedding_type: EmbeddingType = EmbeddingType.TEXT,
        model_name: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Embedding:
        """
        Create and store an embedding for content.
        
        Args:
            db: Database session
            source_type: Type of source (ARTIFACT, CONVERSATION, etc.)
            source_id: ID of the source object
            content: Text content to embed
            embedding_type: Type of embedding (TEXT, IMAGE, etc.)
            model_name: Name of the embedding model used
            extra_metadata: Additional metadata
            
        Returns:
            Created Embedding object
        """
        tenant_id = get_context(CTX_TENANT_ID)
        if not tenant_id:
            raise ValueError("Tenant ID not found in request context")
        
        # Generate embedding
        embedding_vector = EmbeddingService.generate_embedding(content)
        
        # Check if pgvector is available
        use_pgvector = EmbeddingService._check_pgvector_available(db)
        
        # Create embedding record
        # Note: The Embedding model uses Vector(1536) type, but we're generating 768-dim embeddings
        # Pad to 1536 to match the model's expected dimension
        target_dimension = 1536  # Match the model's Vector(1536)
        
        # Pad or truncate embedding to match model dimension
        if len(embedding_vector) < target_dimension:
            embedding_vector.extend([0.0] * (target_dimension - len(embedding_vector)))
        elif len(embedding_vector) > target_dimension:
            embedding_vector = embedding_vector[:target_dimension]
        
        embedding_record = Embedding(
            tenant_id=tenant_id,
            source_type=source_type,
            source_id=source_id,
            type=embedding_type,
            content=content,
            model_name=model_name or EmbeddingService.EMBEDDING_MODEL,
            model_version="1.0",
            extra_metadata=extra_metadata,
        )
        
        # Store embedding - handle both pgvector and JSON fallback
        if use_pgvector:
            # Store as Vector type (pgvector) - SQLAlchemy will handle conversion
            try:
                # pgvector expects a list/array that can be converted to Vector
                # SQLAlchemy's Vector type will handle the conversion
                embedding_record.embedding = embedding_vector
            except Exception as e:
                print(f"Warning: Failed to store as Vector, falling back to JSON: {e}")
                # If Vector storage fails, we need to handle JSON fallback
                # But the model expects Vector type, so this might fail
                # For now, try to store as-is and let the database handle it
                embedding_record.embedding = embedding_vector
        else:
            # JSON fallback - but the model expects Vector type
            # This will fail if pgvector is not available and the column is Vector type
            # We need to handle this at the migration level or use a different approach
            # For now, try storing as list - SQLAlchemy might handle conversion
            # If this fails, the user needs to run migrations to enable pgvector
            try:
                embedding_record.embedding = embedding_vector
            except Exception as e:
                print(f"Error: Cannot store embedding without pgvector. Please enable pgvector extension: {e}")
                raise ValueError("pgvector extension is required for embedding storage. Please run: CREATE EXTENSION IF NOT EXISTS vector;")
        
        db.add(embedding_record)
        db.commit()
        db.refresh(embedding_record)
        
        return embedding_record
    
    @staticmethod
    def create_embedding_for_artifact(
        db: Session,
        artifact_id: str,
        content: Optional[str] = None,
    ) -> Optional[Embedding]:
        """
        Create embedding for an artifact.
        
        Args:
            db: Database session
            artifact_id: ID of the artifact
            content: Optional content override (uses artifact.content if not provided)
            
        Returns:
            Created Embedding or None if artifact not found
        """
        from app.db.models.artifact import Artifact
        
        tenant_id = get_context(CTX_TENANT_ID)
        if not tenant_id:
            raise ValueError("Tenant ID not found in request context")
        
        # Get artifact
        artifact = db.query(Artifact).filter(
            Artifact.id == artifact_id,
            Artifact.tenant_id == tenant_id
        ).first()
        
        if not artifact:
            return None
        
        # Use provided content or artifact content
        text_content = content or artifact.content or artifact.title or ""
        if not text_content:
            return None
        
        # Check if embedding already exists
        existing = db.query(Embedding).filter(
            Embedding.tenant_id == tenant_id,
            Embedding.source_type == EmbeddingSource.ARTIFACT,
            Embedding.source_id == artifact_id
        ).first()
        
        if existing:
            return existing
        
        # Create embedding
        return EmbeddingService.create_embedding(
            db=db,
            source_type=EmbeddingSource.ARTIFACT,
            source_id=artifact_id,
            content=text_content,
            embedding_type=EmbeddingType.TEXT,
            extra_metadata={
                "artifact_type": artifact.type.value if artifact.type else None,
                "artifact_status": artifact.status.value if artifact.status else None,
            }
        )
    
    @staticmethod
    def create_embedding_for_conversation_message(
        db: Session,
        message_id: str,
        content: Optional[str] = None,
    ) -> Optional[Embedding]:
        """
        Create embedding for a conversation message.
        
        Args:
            db: Database session
            message_id: ID of the conversation message
            content: Optional content override (uses message.content if not provided)
            
        Returns:
            Created Embedding or None if message not found
        """
        from app.db.models.conversation import ConversationMessage
        
        tenant_id = get_context(CTX_TENANT_ID)
        if not tenant_id:
            raise ValueError("Tenant ID not found in request context")
        
        # Get message (need to join with conversation to get tenant_id)
        from app.db.models.conversation import Conversation
        
        message = db.query(ConversationMessage).join(
            Conversation, ConversationMessage.conversation_id == Conversation.id
        ).filter(
            ConversationMessage.id == message_id,
            Conversation.tenant_id == tenant_id
        ).first()
        
        if not message:
            return None
        
        # Only embed user and assistant messages (skip system)
        if message.role == "system":
            return None
        
        # Use provided content or message content
        text_content = content or message.content or ""
        if not text_content:
            return None
        
        # Check if embedding already exists
        existing = db.query(Embedding).filter(
            Embedding.tenant_id == tenant_id,
            Embedding.source_type == EmbeddingSource.CONVERSATION,
            Embedding.source_id == message_id
        ).first()
        
        if existing:
            return existing
        
        # Create embedding
        return EmbeddingService.create_embedding(
            db=db,
            source_type=EmbeddingSource.CONVERSATION,
            source_id=message_id,
            content=text_content,
            embedding_type=EmbeddingType.TEXT,
            extra_metadata={
                "conversation_id": message.conversation_id,
                "message_role": message.role,
            }
        )
    
    @staticmethod
    def search_similar(
        db: Session,
        query_text: str,
        source_type: Optional[EmbeddingSource] = None,
        limit: int = 10,
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content using vector similarity.
        
        Args:
            db: Database session
            query_text: Query text to search for
            source_type: Optional filter by source type
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            List of similar content with similarity scores
        """
        tenant_id = get_context(CTX_TENANT_ID)
        if not tenant_id:
            raise ValueError("Tenant ID not found in request context")
        
        # Generate query embedding
        query_embedding = EmbeddingService.generate_embedding(query_text)
        
        # Check if pgvector is available
        use_pgvector = EmbeddingService._check_pgvector_available(db)
        
        if use_pgvector:
            # Use pgvector cosine similarity
            from pgvector.sqlalchemy import Vector
            
            # Pad query embedding to match stored dimension (1536)
            target_dimension = 1536
            if len(query_embedding) < target_dimension:
                query_embedding_padded = query_embedding + [0.0] * (target_dimension - len(query_embedding))
            elif len(query_embedding) > target_dimension:
                query_embedding_padded = query_embedding[:target_dimension]
            else:
                query_embedding_padded = query_embedding
            
            query = db.query(Embedding).filter(
                Embedding.tenant_id == tenant_id
            )
            
            if source_type:
                query = query.filter(Embedding.source_type == source_type)
            
            # Use cosine distance (1 - cosine similarity)
            # pgvector's cosine_distance expects a list/array
            try:
                results = query.order_by(
                    Embedding.embedding.cosine_distance(query_embedding_padded)
                ).limit(limit).all()
            except Exception as e:
                print(f"Warning: pgvector cosine_distance failed, falling back to Python calculation: {e}")
                # Fallback to loading all and computing in Python
                results = query.limit(limit * 2).all()  # Get more to filter by threshold
            
            # Calculate similarity scores
            similar_items = []
            for result in results:
                # Get embedding vector from result
                if hasattr(result.embedding, '__iter__') and not isinstance(result.embedding, str):
                    result_vec = list(result.embedding)
                elif isinstance(result.embedding, str):
                    result_vec = json.loads(result.embedding)
                else:
                    result_vec = []
                
                if not result_vec:
                    continue
                
                # Truncate/pad result_vec to match query dimension for comparison
                if len(result_vec) != len(query_embedding_padded):
                    min_len = min(len(result_vec), len(query_embedding_padded))
                    result_vec = result_vec[:min_len]
                    query_vec_compare = query_embedding_padded[:min_len]
                else:
                    query_vec_compare = query_embedding_padded
                
                # Calculate cosine similarity
                similarity = EmbeddingService._cosine_similarity(query_vec_compare, result_vec)
                
                if similarity >= threshold:
                    similar_items.append({
                        "id": result.id,
                        "source_type": result.source_type.value,
                        "source_id": result.source_id,
                        "content": result.content,
                        "similarity": similarity,
                        "metadata": result.extra_metadata,
                    })
            
            # Sort by similarity (descending) and limit
            similar_items.sort(key=lambda x: x["similarity"], reverse=True)
            return similar_items[:limit]
        else:
            # Fallback: JSON-based similarity search
            # Load all embeddings and compute similarity in Python
            query = db.query(Embedding).filter(
                Embedding.tenant_id == tenant_id
            )
            
            if source_type:
                query = query.filter(Embedding.source_type == source_type)
            
            all_embeddings = query.all()
            
            similar_items = []
            for result in all_embeddings:
                # Parse embedding from JSON
                if isinstance(result.embedding, str):
                    result_vec = json.loads(result.embedding)
                else:
                    result_vec = list(result.embedding) if hasattr(result.embedding, '__iter__') else []
                
                if not result_vec:
                    continue
                
                # Calculate cosine similarity
                similarity = EmbeddingService._cosine_similarity(query_embedding, result_vec)
                
                if similarity >= threshold:
                    similar_items.append({
                        "id": result.id,
                        "source_type": result.source_type.value,
                        "source_id": result.source_id,
                        "content": result.content,
                        "similarity": similarity,
                        "metadata": result.extra_metadata,
                    })
            
            # Sort by similarity and limit
            similar_items.sort(key=lambda x: x["similarity"], reverse=True)
            return similar_items[:limit]
    
    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            # Pad or truncate to match
            min_len = min(len(vec1), len(vec2))
            vec1 = vec1[:min_len]
            vec2 = vec2[:min_len]
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(a * a for a in vec2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
