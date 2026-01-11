"""
Usage API endpoints - Track and query LLM usage.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db.session import get_db
from app.db.models.user import User
from app.services.usage_service import UsageService
from app.dependencies.auth import get_current_user, require_project
from app.db.models.project import Project

router = APIRouter(prefix="/projects/{project_id}/usage", tags=["Usage"])


@router.get("/stats")
def get_usage_stats(
    project_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Get usage statistics for current tenant."""
    try:
        stats = UsageService.get_usage_stats(
            db=db,
            tenant_id=current_user.tenant_id,
            start_date=start_date,
            end_date=end_date,
        )
        return {"success": True, **stats}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
