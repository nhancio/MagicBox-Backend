"""
Credit Transaction model - tracks credit transactions (deposits, withdrawals).
"""
from sqlalchemy import Column, String, ForeignKey, DateTime, Float, Enum, Text
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class TransactionType(str, enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    credit_account_id = Column(String, ForeignKey("credit_accounts.id"), nullable=False, index=True)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    amount = Column(Float, nullable=False)  # Positive for deposits, negative for withdrawals
    balance_after = Column(Float, nullable=False)  # Balance after this transaction
    
    # Reference
    reference_id = Column(String, nullable=True)  # e.g., invoice_id, run_id
    reference_type = Column(String, nullable=True)  # e.g., "invoice", "run", "manual"
    
    # Description
    description = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)

