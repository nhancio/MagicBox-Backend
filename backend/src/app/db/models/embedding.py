"""
Embedding model - stores vector embeddings for RAG (Retrieval Augmented Generation).
Supports text, image, and video embeddings stored in pgvector.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Integer, Enum, JSON
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class EmbeddingType(str, enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"


class EmbeddingSource(str, enum.Enum):
    CONVERSATION = "CONVERSATION"
    ARTIFACT = "ARTIFACT"
    BRAND_PERSONA = "BRAND_PERSONA"
    PROJECT = "PROJECT"
    OTHER = "OTHER"


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Source reference
    source_type = Column(Enum(EmbeddingSource), nullable=False, index=True)
    source_id = Column(String, nullable=False, index=True)  # ID of source (conversation, artifact, etc.)
    
    # Embedding data
    type = Column(Enum(EmbeddingType), nullable=False)
    content = Column(Text, nullable=True)  # Original text content
    embedding = Column(Vector(1536), nullable=False)  # Vector embedding (OpenAI default is 1536)
    
    # Model information
    model_name = Column(String, nullable=False)  # e.g., "text-embedding-ada-002"
    model_version = Column(String, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="embeddings")

