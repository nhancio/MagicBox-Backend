"""
Social Repository - Data access layer for Social operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.social_account import SocialAccount, SocialPlatform
from app.db.models.social_post import SocialPost


class SocialRepository:
    """Repository for Social operations."""
    
    @staticmethod
    def get_account_by_id(db: Session, account_id: str) -> Optional[SocialAccount]:
        """Get social account by ID."""
        return db.query(SocialAccount).filter(SocialAccount.id == account_id).first()
    
    @staticmethod
    def get_accounts_by_tenant(
        db: Session,
        tenant_id: str,
        platform: Optional[SocialPlatform] = None,
    ) -> List[SocialAccount]:
        """Get social accounts by tenant."""
        query = db.query(SocialAccount).filter(
            SocialAccount.tenant_id == tenant_id,
            SocialAccount.is_connected == True
        )
        
        if platform:
            query = query.filter(SocialAccount.platform == platform)
        
        return query.all()
    
    @staticmethod
    def get_posts_by_tenant(
        db: Session,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SocialPost]:
        """Get social posts by tenant."""
        return db.query(SocialPost).filter(
            SocialPost.tenant_id == tenant_id
        ).order_by(SocialPost.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_account(db: Session, account: SocialAccount) -> SocialAccount:
        """Create social account."""
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    
    @staticmethod
    def create_post(db: Session, post: SocialPost) -> SocialPost:
        """Create social post."""
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
