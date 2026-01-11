"""
Artifact Repository - Data access layer for Artifact operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.artifact import Artifact, ArtifactType, ArtifactStatus


class ArtifactRepository:
    """Repository for Artifact operations."""
    
    @staticmethod
    def get_by_id(db: Session, artifact_id: str) -> Optional[Artifact]:
        """Get artifact by ID."""
        return db.query(Artifact).filter(Artifact.id == artifact_id).first()
    
    @staticmethod
    def get_by_tenant(
        db: Session,
        tenant_id: str,
        artifact_type: Optional[ArtifactType] = None,
        status: Optional[ArtifactStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Artifact]:
        """Get artifacts by tenant."""
        query = db.query(Artifact).filter(Artifact.tenant_id == tenant_id)
        
        if artifact_type:
            query = query.filter(Artifact.type == artifact_type)
        if status:
            query = query.filter(Artifact.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def create(db: Session, artifact: Artifact) -> Artifact:
        """Create artifact."""
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact
    
    @staticmethod
    def update(db: Session, artifact: Artifact) -> Artifact:
        """Update artifact."""
        db.commit()
        db.refresh(artifact)
        return artifact
