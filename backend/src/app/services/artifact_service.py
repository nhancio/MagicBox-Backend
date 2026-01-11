"""
Artifact Service - manages generated outputs (posts, images, videos).
Follows architecture: immutable, versioned artifacts.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db.models.artifact import Artifact, ArtifactType, ArtifactStatus
from app.schemas.artifact import ArtifactCreate, ArtifactUpdate
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID


class ArtifactService:
    """Service for managing artifacts."""

    @staticmethod
    def create_artifact(db: Session, artifact_data: ArtifactCreate, run_id: Optional[str] = None) -> Artifact:
        """Create a new artifact (immutable, version 1)."""
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id:
            raise ValueError("Tenant ID not found in context")
        if not user_id:
            raise ValueError("User ID not found in context")
        
        artifact = Artifact(
            tenant_id=tenant_id,
            project_id=artifact_data.project_id,
            conversation_id=artifact_data.conversation_id,
            user_id=user_id,
            run_id=run_id,
            type=artifact_data.type,
            title=artifact_data.title,
            content=artifact_data.content,
            content_data=artifact_data.content_data,
            tags=artifact_data.tags,
            status=ArtifactStatus.DRAFT,
            version=1,
        )
        
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact

    @staticmethod
    def create_artifact_version(
        db: Session,
        parent_artifact_id: str,
        artifact_data: ArtifactUpdate
    ) -> Artifact:
        """Create a new version of an existing artifact (immutable versioning)."""
        parent = ArtifactService.get_artifact(db, parent_artifact_id)
        if not parent:
            raise ValueError("Parent artifact not found")
        
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        # Get next version number
        max_version = db.query(Artifact).filter(
            Artifact.parent_artifact_id == parent_artifact_id
        ).order_by(Artifact.version.desc()).first()
        
        next_version = (max_version.version + 1) if max_version else parent.version + 1
        
        new_artifact = Artifact(
            tenant_id=tenant_id,
            project_id=parent.project_id,
            conversation_id=parent.conversation_id,
            user_id=user_id,
            run_id=parent.run_id,
            type=parent.type,
            title=artifact_data.title or parent.title,
            content=artifact_data.content or parent.content,
            content_data=parent.content_data,  # Can be updated via metadata
            tags=artifact_data.tags or parent.tags,
            status=artifact_data.status or parent.status,
            version=next_version,
            parent_artifact_id=parent_artifact_id,
            prompt_used=parent.prompt_used,
            model_used=parent.model_used,
        )
        
        db.add(new_artifact)
        db.commit()
        db.refresh(new_artifact)
        return new_artifact

    @staticmethod
    def get_artifact(db: Session, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by ID (tenant-scoped)."""
        tenant_id = get_context(CTX_TENANT_ID)
        
        return db.query(Artifact).filter(
            Artifact.id == artifact_id,
            Artifact.tenant_id == tenant_id
        ).first()

    @staticmethod
    def list_artifacts(
        db: Session,
        project_id: Optional[str] = None,
        artifact_type: Optional[ArtifactType] = None,
        status: Optional[ArtifactStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Artifact]:
        """List artifacts for the current tenant."""
        tenant_id = get_context(CTX_TENANT_ID)
        
        query = db.query(Artifact).filter(
            Artifact.tenant_id == tenant_id
        )
        
        if project_id:
            query = query.filter(Artifact.project_id == project_id)
        if artifact_type:
            query = query.filter(Artifact.type == artifact_type)
        if status:
            query = query.filter(Artifact.status == status)
        
        # Get only latest versions (no parent_artifact_id means it's a root version)
        # For simplicity, we'll get all and filter in application logic
        return query.order_by(Artifact.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_artifact_versions(db: Session, artifact_id: str) -> List[Artifact]:
        """Get all versions of an artifact."""
        artifact = ArtifactService.get_artifact(db, artifact_id)
        if not artifact:
            return []
        
        # Find root artifact
        root_id = artifact.parent_artifact_id or artifact.id
        
        return db.query(Artifact).filter(
            (Artifact.id == root_id) | (Artifact.parent_artifact_id == root_id)
        ).order_by(Artifact.version.asc()).all()

    @staticmethod
    def update_artifact(
        db: Session,
        artifact_id: str,
        artifact_data: ArtifactUpdate
    ) -> Optional[Artifact]:
        """
        Update artifact metadata (not content - artifacts are immutable).
        For content changes, create a new version.
        """
        artifact = ArtifactService.get_artifact(db, artifact_id)
        if not artifact:
            return None
        
        # Only allow updating metadata, not content (immutability)
        update_data = artifact_data.model_dump(exclude_unset=True, exclude={"content"})
        for field, value in update_data.items():
            if hasattr(artifact, field):
                setattr(artifact, field, value)
        
        db.commit()
        db.refresh(artifact)
        return artifact

    @staticmethod
    def publish_artifact(db: Session, artifact_id: str) -> Optional[Artifact]:
        """Publish an artifact."""
        artifact = ArtifactService.get_artifact(db, artifact_id)
        if not artifact:
            return None
        
        artifact.status = ArtifactStatus.PUBLISHED
        artifact.published_at = datetime.utcnow()
        
        db.commit()
        db.refresh(artifact)
        return artifact
