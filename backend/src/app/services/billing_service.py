"""
Billing Service - Manages billing, invoices, and payment processing.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.models.plan import Plan
from app.db.models.tenant import Tenant
from app.services.usage_service import UsageService
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID
import uuid


class BillingService:
    """Service for billing and invoicing."""
    
    @staticmethod
    def get_current_plan(db: Session, tenant_id: Optional[str] = None) -> Optional[Plan]:
        """Get current plan for tenant."""
        if not tenant_id:
            tenant_id = get_context(CTX_TENANT_ID)
        
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant or not tenant.plan_id:
            return None
        
        return db.query(Plan).filter(Plan.id == tenant.plan_id).first()
    
    @staticmethod
    def generate_invoice(
        db: Session,
        tenant_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Invoice:
        """Generate invoice for usage period."""
        if not tenant_id:
            tenant_id = get_context(CTX_TENANT_ID)
        
        if not start_date:
            # Default to last month
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
        elif not end_date:
            end_date = datetime.utcnow()
        
        # Get usage stats
        usage_stats = UsageService.get_usage_stats(
            db=db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Get plan
        plan = BillingService.get_current_plan(db, tenant_id)
        plan_name = plan.name if plan else "Free"
        
        # Calculate amount (usage-based or plan-based)
        amount = usage_stats["total_cost_usd"]
        
        # Create invoice
        invoice = Invoice(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            plan_id=plan.id if plan else None,
            plan_name=plan_name,
            amount=amount,
            status=InvoiceStatus.PENDING,
            due_date=end_date + timedelta(days=30),
            period_start=start_date,
            period_end=end_date,
            usage_summary=usage_stats,
        )
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice
    
    @staticmethod
    def get_invoices(
        db: Session,
        tenant_id: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        limit: int = 50,
    ) -> List[Invoice]:
        """Get invoices for tenant."""
        if not tenant_id:
            tenant_id = get_context(CTX_TENANT_ID)
        
        query = db.query(Invoice).filter(Invoice.tenant_id == tenant_id)
        
        if status:
            query = query.filter(Invoice.status == status)
        
        return query.order_by(Invoice.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def mark_invoice_paid(db: Session, invoice_id: str) -> Invoice:
        """Mark invoice as paid."""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.utcnow()
        db.commit()
        db.refresh(invoice)
        return invoice
