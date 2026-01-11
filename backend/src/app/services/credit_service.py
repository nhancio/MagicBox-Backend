"""
Credit Service - Manages credit/usage tracking and quota enforcement.
Similar to Syntagro's credit system.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from app.db.models.credit_account import CreditAccount
from app.db.models.credit_transaction import CreditTransaction
from app.db.models.quota import Quota
from app.db.models.tenant import Tenant
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID


class CreditService:
    """Service for managing credits and usage tracking."""
    
    # Credit costs per operation
    CREDIT_COSTS = {
        "post_generation": 1,
        "reel_generation": 2,
        "video_generation": 5,
        "story_generation": 1,
        "image_generation": 3,
        "content_edit": 0.5,
        "publish": 0,
    }
    
    @staticmethod
    def get_credit_balance(db: Session, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current credit balance for tenant."""
        if not tenant_id:
            tenant_id = get_context(CTX_TENANT_ID)
        
        if not tenant_id:
            raise ValueError("Tenant ID not found")
        
        account = db.query(CreditAccount).filter(
            CreditAccount.tenant_id == tenant_id,
            CreditAccount.is_active == True
        ).first()
        
        if not account:
            # Create default account with 0 credits
            account = CreditAccount(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                balance=0.0,
            )
            db.add(account)
            db.commit()
            db.refresh(account)
        
        return {
            "balance": float(account.balance),
            "currency": account.currency,
            "is_active": account.is_active,
        }
    
    @staticmethod
    def add_credits(
        db: Session,
        amount: float,
        reason: str = "purchase",
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add credits to account."""
        if not tenant_id:
            tenant_id = get_context(CTX_TENANT_ID)
        
        account = CreditService._get_or_create_account(db, tenant_id)
        
        # Add credits
        account.balance += amount
        account.updated_at = datetime.utcnow()
        
        # Create transaction record
        from app.db.models.credit_transaction import TransactionType
        transaction = CreditTransaction(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            credit_account_id=account.id,
            amount=amount,
            transaction_type=TransactionType.DEPOSIT,
            balance_after=float(account.balance),
            description=reason,
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(account)
        
        return {
            "success": True,
            "new_balance": float(account.balance),
            "transaction_id": transaction.id,
        }
    
    @staticmethod
    def deduct_credits(
        db: Session,
        operation: str,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Deduct credits for an operation."""
        if not tenant_id:
            tenant_id = get_context(CTX_TENANT_ID)
        
        cost = CreditService.CREDIT_COSTS.get(operation, 0)
        if cost == 0:
            return {"success": True, "cost": 0, "balance": None}
        
        account = CreditService._get_or_create_account(db, tenant_id)
        
        if account.balance < cost:
            return {
                "success": False,
                "error": "Insufficient credits",
                "required": cost,
                "balance": float(account.balance),
            }
        
        # Deduct credits
        account.balance -= cost
        account.updated_at = datetime.utcnow()
        
        # Create transaction record
        from app.db.models.credit_transaction import TransactionType
        transaction = CreditTransaction(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            credit_account_id=account.id,
            amount=-cost,
            transaction_type=TransactionType.WITHDRAWAL,
            balance_after=float(account.balance),
            description=operation,
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(account)
        
        return {
            "success": True,
            "cost": cost,
            "new_balance": float(account.balance),
            "transaction_id": transaction.id,
        }
    
    @staticmethod
    def check_credits_available(
        db: Session,
        operation: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Check if tenant has enough credits for operation."""
        if not tenant_id:
            tenant_id = get_context(CTX_TENANT_ID)
        
        cost = CreditService.CREDIT_COSTS.get(operation, 0)
        if cost == 0:
            return True
        
        account = CreditService._get_or_create_account(db, tenant_id)
        return account.balance >= cost
    
    @staticmethod
    def _get_or_create_account(db: Session, tenant_id: str) -> CreditAccount:
        """Get or create credit account for tenant."""
        account = db.query(CreditAccount).filter(
            CreditAccount.tenant_id == tenant_id,
            CreditAccount.is_active == True
        ).first()
        
        if not account:
            account = CreditAccount(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                balance=0.0,
            )
            db.add(account)
            db.commit()
            db.refresh(account)
        
        return account
    
    @staticmethod
    def get_usage_history(
        db: Session,
        tenant_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get credit usage history."""
        if not tenant_id:
            tenant_id = get_context(CTX_TENANT_ID)
        
        since = datetime.utcnow() - timedelta(days=days)
        
        from app.db.models.credit_transaction import TransactionType
        transactions = db.query(CreditTransaction).filter(
            CreditTransaction.tenant_id == tenant_id,
            CreditTransaction.created_at >= since,
            CreditTransaction.transaction_type == TransactionType.WITHDRAWAL
        ).order_by(CreditTransaction.created_at.desc()).all()
        
        return {
            "period_days": days,
            "total_spent": sum(abs(t.amount) for t in transactions),
            "transactions": [
                {
                    "id": t.id,
                    "amount": float(abs(t.amount)),
                    "description": t.description,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in transactions
            ]
        }
