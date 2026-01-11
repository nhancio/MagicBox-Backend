"""
Projects API endpoints - manage brands/workspaces.
Requires authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models.user import User
from app.services.project_service import ProjectService
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectRead
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new project (brand/workspace)."""
    try:
        project = ProjectService.create_project(db, project_data)
        return project
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ProjectRead])
def list_projects(
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all projects for the current tenant."""
    projects = ProjectService.list_projects(db, skip=skip, limit=limit)
    return projects


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a project by ID."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a project."""
    project = ProjectService.update_project(db, project_id, project_data)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a project (soft delete)."""
    success = ProjectService.delete_project(db, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return None
