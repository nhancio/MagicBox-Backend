"""
Invoice model - billing invoices for tenants.
"""
from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Float, Enum, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import uuid
import enum


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Invoice details
    invoice_number = Column(String, nullable=False, unique=True)  # e.g., "INV-2024-001"
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False, index=True)
    
    # Billing period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Amounts
    subtotal_usd = Column(Float, nullable=False)
    tax_usd = Column(Float, default=0.0, nullable=False)
    total_usd = Column(Float, nullable=False)
    
    # Payment
    paid_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=False)
    
    # Line items (JSON array)
    line_items = Column(JSON, nullable=True)  # Detailed line items
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="invoices")

