"""
Run Repository - Data access layer for Run operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.run import Run, RunStatus


class RunRepository:
    """Repository for Run operations."""
    
    @staticmethod
    def get_by_id(db: Session, run_id: str) -> Optional[Run]:
        """Get run by ID."""
        return db.query(Run).filter(Run.id == run_id).first()
    
    @staticmethod
    def get_by_tenant(
        db: Session,
        tenant_id: str,
        status: Optional[RunStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Run]:
        """Get runs by tenant."""
        query = db.query(Run).filter(Run.tenant_id == tenant_id)
        
        if status:
            query = query.filter(Run.status == status)
        
        return query.order_by(Run.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def create(db: Session, run: Run) -> Run:
        """Create run."""
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
    
    @staticmethod
    def update(db: Session, run: Run) -> Run:
        """Update run."""
        db.commit()
        db.refresh(run)
        return run
