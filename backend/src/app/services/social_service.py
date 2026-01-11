"""
Social Media Service - Manages social media account connections and publishing.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.db.models.social_account import SocialAccount, SocialPlatform
from app.db.models.social_post import SocialPost, PostStatus
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID
from app.integrations.facebook import FacebookIntegration
from app.integrations.instagram import InstagramIntegration
from app.integrations.linkedin import LinkedInIntegration
from app.integrations.twitter import TwitterIntegration
from app.integrations.tiktok import TikTokIntegration
from app.security.encryption import encrypt_token, decrypt_token

# YouTube integration (optional)
try:
    from app.integrations.youtube import YouTubeIntegration
except ImportError:
    YouTubeIntegration = None


class SocialService:
    """Service for managing social media accounts and publishing."""
    
    @staticmethod
    def get_integration(platform: SocialPlatform):
        """Get the appropriate integration class for a platform."""
        integrations = {
            SocialPlatform.FACEBOOK: FacebookIntegration,
            SocialPlatform.INSTAGRAM: InstagramIntegration,
            SocialPlatform.LINKEDIN: LinkedInIntegration,
            SocialPlatform.TWITTER: TwitterIntegration,
            SocialPlatform.TIKTOK: TikTokIntegration,
        }
        
        if platform == SocialPlatform.YOUTUBE:
            if YouTubeIntegration:
                integrations[SocialPlatform.YOUTUBE] = YouTubeIntegration
            else:
                raise ImportError("YouTube integration requires google-api-python-client. Install: pip install google-api-python-client google-auth google-auth-oauthlib")
        
        return integrations.get(platform)
    
    @staticmethod
    def connect_account(
        db: Session,
        platform: SocialPlatform,
        account_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        account_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SocialAccount:
        """
        Connect a social media account.
        
        Args:
            db: Database session
            platform: Social media platform
            account_name: Display name for the account
            access_token: OAuth access token
            refresh_token: OAuth refresh token (if available)
            account_id: Platform-specific account ID
            metadata: Additional platform-specific metadata
        
        Returns:
            Created SocialAccount
        """
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id or not user_id:
            raise ValueError("Tenant ID and User ID must be in request context")
        
        enc_access = encrypt_token(access_token)
        enc_refresh = encrypt_token(refresh_token) if refresh_token else None

        # Check if account already exists
        existing = db.query(SocialAccount).filter(
            SocialAccount.tenant_id == tenant_id,
            SocialAccount.platform == platform,
            SocialAccount.account_id == account_id
        ).first()
        
        if existing:
            # Update existing account
            existing.access_token = enc_access
            existing.refresh_token = enc_refresh
            existing.account_id = account_id
            existing.account_name = account_name
            existing.is_connected = True
            existing.is_active = True
            existing.extra_metadata = metadata or existing.extra_metadata
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new account
        account = SocialAccount(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            platform=platform,
            account_name=account_name,
            account_id=account_id,
            access_token=enc_access,
            refresh_token=enc_refresh,
            is_connected=True,
            is_active=True,
            extra_metadata=metadata,
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def connect_account_for_tenant_user(
        db: Session,
        tenant_id: str,
        user_id: str,
        platform: SocialPlatform,
        account_name: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        account_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SocialAccount:
        """
        Same as connect_account(), but does NOT rely on request context.
        Used by OAuth callback handlers (no JWT on callback).
        """
        enc_access = encrypt_token(access_token)
        enc_refresh = encrypt_token(refresh_token) if refresh_token else None

        existing = db.query(SocialAccount).filter(
            SocialAccount.tenant_id == tenant_id,
            SocialAccount.platform == platform,
            SocialAccount.account_id == account_id
        ).first()

        if existing:
            existing.access_token = enc_access
            existing.refresh_token = enc_refresh
            existing.account_id = account_id
            existing.account_name = account_name
            existing.is_connected = True
            existing.is_active = True
            existing.extra_metadata = metadata or existing.extra_metadata
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing

        account = SocialAccount(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            platform=platform,
            account_name=account_name,
            account_id=account_id,
            access_token=enc_access,
            refresh_token=enc_refresh,
            is_connected=True,
            is_active=True,
            extra_metadata=metadata,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    
    @staticmethod
    def list_accounts(
        db: Session,
        platform: Optional[SocialPlatform] = None,
        active_only: bool = True,
    ) -> List[SocialAccount]:
        """List social media accounts for the current tenant."""
        tenant_id = get_context(CTX_TENANT_ID)
        if not tenant_id:
            raise ValueError("Tenant ID not found in request context")
        
        query = db.query(SocialAccount).filter(
            SocialAccount.tenant_id == tenant_id
        )
        
        if platform:
            query = query.filter(SocialAccount.platform == platform)
        
        if active_only:
            query = query.filter(SocialAccount.is_active == True)
        
        return query.all()
    
    @staticmethod
    def disconnect_account(db: Session, account_id: str) -> bool:
        """Disconnect a social media account."""
        tenant_id = get_context(CTX_TENANT_ID)
        if not tenant_id:
            raise ValueError("Tenant ID not found in request context")
        
        account = db.query(SocialAccount).filter(
            SocialAccount.id == account_id,
            SocialAccount.tenant_id == tenant_id
        ).first()
        
        if not account:
            return False
        
        account.is_connected = False
        account.is_active = False
        account.access_token = None
        account.refresh_token = None
        account.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    @staticmethod
    def publish_post(
        db: Session,
        account_id: str,
        content: str,
        media_urls: Optional[List[str]] = None,
        scheduled_at: Optional[datetime] = None,
    ) -> SocialPost:
        """
        Publish a post to a social media platform.
        
        Args:
            db: Database session
            account_id: Social account ID to publish to
            content: Post content/text
            media_urls: Optional list of media URLs
            scheduled_at: Optional scheduled publish time
        
        Returns:
            Created SocialPost
        """
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id or not user_id:
            raise ValueError("Tenant ID and User ID must be in request context")
        
        # Get social account
        account = db.query(SocialAccount).filter(
            SocialAccount.id == account_id,
            SocialAccount.tenant_id == tenant_id,
            SocialAccount.is_connected == True
        ).first()
        
        if not account:
            raise ValueError("Social account not found or not connected")
        
        # Create post record
        post = SocialPost(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            social_account_id=account_id,
            content=content,
            media_urls=media_urls or [],
            status=PostStatus.SCHEDULED if scheduled_at else PostStatus.DRAFT,
            scheduled_at=scheduled_at,
            created_by=user_id,
        )
        
        db.add(post)
        db.commit()
        db.refresh(post)
        
        # If not scheduled, publish immediately
        if not scheduled_at:
            SocialService._publish_now(db, post, account)
        
        return post
    
    @staticmethod
    def _publish_now(db: Session, post: SocialPost, account: SocialAccount):
        """Publish a post immediately using the appropriate integration."""
        integration_class = SocialService.get_integration(account.platform)
        if not integration_class:
            raise ValueError(f"No integration available for platform: {account.platform}")
        
        # Decrypt tokens for use with external APIs
        access_token = decrypt_token(account.access_token)
        refresh_token = decrypt_token(account.refresh_token)

        # Initialize integration with access token
        if account.platform == SocialPlatform.YOUTUBE:
            integration = integration_class(access_token, refresh_token)
        elif account.platform == SocialPlatform.INSTAGRAM:
            # Instagram may need account_id from metadata
            account_id = account.extra_metadata.get("instagram_account_id") if account.extra_metadata else None
            integration = integration_class(access_token, account_id)
        elif account.platform == SocialPlatform.TIKTOK:
            advertiser_id = account.extra_metadata.get("advertiser_id") if account.extra_metadata else None
            integration = integration_class(access_token, advertiser_id)
        elif account.platform == SocialPlatform.FACEBOOK:
            integration = integration_class(access_token)
        else:
            integration = integration_class(access_token)
        
        try:
            post.status = PostStatus.PUBLISHING
            db.commit()
            
            # Publish using integration
            if account.platform == SocialPlatform.FACEBOOK:
                page_id = account.extra_metadata.get("page_id") if account.extra_metadata else None
                result = integration.publish_post(
                    content=post.content,
                    media_urls=post.media_urls or [],
                    page_id=page_id,
                )
            else:
                result = integration.publish_post(
                    content=post.content,
                    media_urls=post.media_urls or [],
                )
            
            # Update post with result
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.utcnow()
            post.external_post_id = result.get("post_id")
            post.external_url = result.get("post_url")
            post.extra_metadata = result.get("metadata", {})
            
        except Exception as e:
            post.status = PostStatus.FAILED
            post.error_message = str(e)
            post.retry_count += 1
            raise
        
        finally:
            db.commit()
    
    @staticmethod
    def get_post_analytics(db: Session, post_id: str) -> Dict[str, Any]:
        """Get analytics for a published post."""
        tenant_id = get_context(CTX_TENANT_ID)
        if not tenant_id:
            raise ValueError("Tenant ID not found in request context")
        
        post = db.query(SocialPost).filter(
            SocialPost.id == post_id,
            SocialPost.tenant_id == tenant_id
        ).first()
        
        if not post:
            raise ValueError("Post not found")
        
        if post.status != PostStatus.PUBLISHED:
            raise ValueError("Post is not published yet")
        
        account = db.query(SocialAccount).filter(
            SocialAccount.id == post.social_account_id
        ).first()
        
        if not account:
            raise ValueError("Social account not found")
        
        # Get analytics from platform
        integration_class = SocialService.get_integration(account.platform)
        if not integration_class:
            raise ValueError(f"No integration available for platform: {account.platform}")
        
        # Initialize integration
        if account.platform == SocialPlatform.YOUTUBE:
            integration = integration_class(account.access_token, account.refresh_token)
        elif account.platform == SocialPlatform.INSTAGRAM:
            account_id = account.extra_metadata.get("instagram_account_id") if account.extra_metadata else None
            integration = integration_class(account.access_token, account_id)
        elif account.platform == SocialPlatform.TIKTOK:
            advertiser_id = account.extra_metadata.get("advertiser_id") if account.extra_metadata else None
            integration = integration_class(account.access_token, advertiser_id)
        else:
            integration = integration_class(account.access_token)
        
        analytics = integration.get_post_analytics(post.external_post_id)
        
        # Update post metrics
        post.likes_count = analytics.get("likes", 0)
        post.comments_count = analytics.get("comments", 0)
        post.shares_count = analytics.get("shares", 0)
        post.views_count = analytics.get("views", 0)
        db.commit()
        
        return analytics
