"""
Tenant Repository - Data access layer for Tenant operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.tenant import Tenant


class TenantRepository:
    """Repository for Tenant operations."""
    
    @staticmethod
    def get_by_id(db: Session, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        return db.query(Tenant).filter(Tenant.slug == slug).first()
    
    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """List all tenants."""
        return db.query(Tenant).offset(skip).limit(limit).all()
    
    @staticmethod
    def create(db: Session, tenant: Tenant) -> Tenant:
        """Create tenant."""
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        return tenant
    
    @staticmethod
    def update(db: Session, tenant: Tenant) -> Tenant:
        """Update tenant."""
        db.commit()
        db.refresh(tenant)
        return tenant
