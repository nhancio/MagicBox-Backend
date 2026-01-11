"""
Billing API endpoints - Manage invoices and billing.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.services.billing_service import BillingService
from app.dependencies.auth import get_current_user, require_project
from app.db.models.project import Project

router = APIRouter(prefix="/projects/{project_id}/billing", tags=["Billing"])


@router.get("/plan")
def get_current_plan(
    project_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Get current plan for tenant."""
    plan = BillingService.get_current_plan(db, tenant_id=current_user.tenant_id)
    if not plan:
        return {"success": False, "plan": None}
    return {"success": True, "plan": {"id": plan.id, "name": plan.name}}


@router.get("/invoices")
def get_invoices(
    project_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Get invoices for tenant."""
    invoices = BillingService.get_invoices(db, tenant_id=current_user.tenant_id)
    return {
        "success": True,
        "invoices": [
            {
                "id": inv.id,
                "amount": inv.amount,
                "status": inv.status.value,
                "due_date": inv.due_date.isoformat() if inv.due_date else None,
            }
            for inv in invoices
        ]
    }


@router.post("/invoices/generate")
def generate_invoice(
    project_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Generate invoice for current period."""
    try:
        invoice = BillingService.generate_invoice(db, tenant_id=current_user.tenant_id)
        return {
            "success": True,
            "invoice": {
                "id": invoice.id,
                "amount": invoice.amount,
                "status": invoice.status.value,
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )