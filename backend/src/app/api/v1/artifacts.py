"""
Artifacts API endpoints - manage generated outputs (posts, images, videos).
Requires authentication and an active project.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.services.artifact_service import ArtifactService
from app.schemas.artifact import ArtifactCreate, ArtifactUpdate, ArtifactRead
from app.db.models.artifact import ArtifactType, ArtifactStatus
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.post("/", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
def create_artifact(
    artifact_data: ArtifactCreate,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Create a new artifact. Requires authentication and a project."""
    try:
        # Ensure artifact is associated with the current project if not specified
        if not artifact_data.project_id:
            artifact_data.project_id = current_project.id
        
        artifact = ArtifactService.create_artifact(db, artifact_data)
        return artifact
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ArtifactRead])
def list_artifacts(
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    project_id: Optional[str] = None,
    artifact_type: Optional[ArtifactType] = None,
    status: Optional[ArtifactStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List artifacts for the current tenant. Requires authentication and a project."""
    # Use current project if project_id not specified
    if not project_id:
        project_id = current_project.id
    
    artifacts = ArtifactService.list_artifacts(
        db,
        project_id=project_id,
        artifact_type=artifact_type,
        status=status,
        skip=skip,
        limit=limit
    )
    return artifacts


@router.get("/{artifact_id}", response_model=ArtifactRead)
def get_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Get an artifact by ID. Requires authentication and a project."""
    artifact = ArtifactService.get_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )
    return artifact


@router.get("/{artifact_id}/versions", response_model=List[ArtifactRead])
def get_artifact_versions(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Get all versions of an artifact. Requires authentication and a project."""
    versions = ArtifactService.get_artifact_versions(db, artifact_id)
    return versions


@router.post("/{artifact_id}/versions", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
def create_artifact_version(
    artifact_id: str,
    artifact_data: ArtifactUpdate,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Create a new version of an artifact. Requires authentication and a project."""
    try:
        artifact = ArtifactService.create_artifact_version(db, artifact_id, artifact_data)
        return artifact
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{artifact_id}", response_model=ArtifactRead)
def update_artifact(
    artifact_id: str,
    artifact_data: ArtifactUpdate,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Update artifact metadata. Requires authentication and a project."""
    artifact = ArtifactService.update_artifact(db, artifact_id, artifact_data)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )
    return artifact


@router.post("/{artifact_id}/publish", response_model=ArtifactRead)
def publish_artifact(
    artifact_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Publish an artifact. Requires authentication and a project."""
    artifact = ArtifactService.publish_artifact(db, artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )
    return artifact
