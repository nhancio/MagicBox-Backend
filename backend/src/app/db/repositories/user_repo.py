"""
User Repository - Data access layer for User operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.user import User


class UserRepository:
    """Repository for User operations."""
    
    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_by_tenant(db: Session, tenant_id: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by tenant."""
        return db.query(User).filter(User.tenant_id == tenant_id).offset(skip).limit(limit).all()
    
    @staticmethod
    def create(db: Session, user: User) -> User:
        """Create user."""
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def update(db: Session, user: User) -> User:
        """Update user."""
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def delete(db: Session, user_id: str) -> bool:
        """Delete user."""
        user = UserRepository.get_by_id(db, user_id)
        if user:
            db.delete(user)
            db.commit()
            return True
        return False
