"""
Credit Repository - Data access layer for Credit operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.credit_account import CreditAccount
from app.db.models.credit_transaction import CreditTransaction


class CreditRepository:
    """Repository for Credit operations."""
    
    @staticmethod
    def get_account_by_tenant(db: Session, tenant_id: str) -> Optional[CreditAccount]:
        """Get credit account by tenant."""
        return db.query(CreditAccount).filter(
            CreditAccount.tenant_id == tenant_id,
            CreditAccount.is_active == True
        ).first()
    
    @staticmethod
    def get_transactions(
        db: Session,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CreditTransaction]:
        """Get credit transactions."""
        return db.query(CreditTransaction).filter(
            CreditTransaction.tenant_id == tenant_id
        ).order_by(CreditTransaction.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_account(db: Session, account: CreditAccount) -> CreditAccount:
        """Create credit account."""
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    
    @staticmethod
    def create_transaction(db: Session, transaction: CreditTransaction) -> CreditTransaction:
        """Create credit transaction."""
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction
