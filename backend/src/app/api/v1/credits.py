"""
Credits API - Manage credit balance and usage.
Similar to Syntagro's credit system.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.services.credit_service import CreditService
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/projects/{project_id}/credits", tags=["Credits"])


class AddCreditsRequest(BaseModel):
    amount: float = Field(..., description="Amount of credits to add", example=100.0)
    reason: str = Field(default="purchase", description="Reason for adding credits")


@router.get("/balance")
def get_balance(
    project_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Get current credit balance.
    Requires authentication and a project.
    """
    try:
        balance = CreditService.get_credit_balance(db)
        return {
            "success": True,
            "balance": balance["balance"],
            "currency": balance["currency"],
            "is_active": balance["is_active"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get balance: {str(e)}"
        )


@router.post("/add")
def add_credits(
    request: AddCreditsRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Add credits to account.
    Requires authentication and ADMIN/OWNER role.
    """
    # Check if user is admin or owner
    if current_user.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only OWNER and ADMIN can add credits"
        )
    
    try:
        result = CreditService.add_credits(
            db=db,
            amount=request.amount,
            reason=request.reason,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add credits: {str(e)}"
        )


@router.get("/usage")
def get_usage_history(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Get credit usage history.
    Requires authentication and a project.
    """
    try:
        history = CreditService.get_usage_history(db, days=days)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage history: {str(e)}"
        )
