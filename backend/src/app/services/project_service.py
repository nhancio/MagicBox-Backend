"""
Project Service - manages brands/workspaces within tenants.
Follows architecture: multi-tenant, AI-first design.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models.project import Project
from app.db.models.brand_persona import BrandPersona
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID


class ProjectService:
    """Service for managing projects (brands/workspaces)."""

    @staticmethod
    def create_project(db: Session, project_data: ProjectCreate) -> Project:
        """Create a new project for the current tenant."""
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id:
            raise ValueError("Tenant ID not found in context")
        
        project = Project(
            tenant_id=tenant_id,
            name=project_data.name,
            description=project_data.description,
            brand_voice=project_data.brand_voice,
            target_audience=project_data.target_audience,
            brand_guidelines=project_data.brand_guidelines,
            created_by=user_id,
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project(db: Session, project_id: str) -> Optional[Project]:
        """Get a project by ID (tenant-scoped)."""
        tenant_id = get_context(CTX_TENANT_ID)
        
        return db.query(Project).filter(
            Project.id == project_id,
            Project.tenant_id == tenant_id
        ).first()

    @staticmethod
    def list_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        """List all projects for the current tenant."""
        tenant_id = get_context(CTX_TENANT_ID)
        
        return db.query(Project).filter(
            Project.tenant_id == tenant_id,
            Project.is_active == True
        ).offset(skip).limit(limit).all()

    @staticmethod
    def update_project(db: Session, project_id: str, project_data: ProjectUpdate) -> Optional[Project]:
        """Update a project (tenant-scoped)."""
        project = ProjectService.get_project(db, project_id)
        if not project:
            return None
        
        update_data = project_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: str) -> bool:
        """Soft delete a project (sets is_active=False)."""
        project = ProjectService.get_project(db, project_id)
        if not project:
            return False
        
        project.is_active = False
        db.commit()
        return True
