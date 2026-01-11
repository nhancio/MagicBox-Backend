"""
Integration Factory - Creates integration instances from connector configurations.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.services.connector_service import ConnectorService
from app.db.models.connector import ConnectorType
from app.integrations.facebook import FacebookIntegration
from app.integrations.instagram import InstagramIntegration
from app.integrations.twitter import TwitterIntegration
from app.integrations.linkedin import LinkedInIntegration
from app.integrations.youtube import YouTubeIntegration
from app.integrations.tiktok import TikTokIntegration


class IntegrationFactory:
    """Factory for creating integration instances from connectors."""
    
    @staticmethod
    def create_integration(
        db: Session,
        connector_id: str,
    ) -> Any:
        """
        Create an integration instance from a connector configuration.
        
        Args:
            db: Database session
            connector_id: Connector ID
            
        Returns:
            Integration instance
        """
        connector = ConnectorService.get_connector(db, connector_id)
        if not connector:
            raise ValueError(f"Connector {connector_id} not found")
        
        if connector.status.value != "ACTIVE":
            raise ValueError(f"Connector {connector_id} is not active")
        
        # Get decrypted config
        config = ConnectorService.get_connector_config_for_integration(db, connector_id)
        
        # Create integration based on connector type
        if connector.connector_type == ConnectorType.FACEBOOK:
            access_token = config.get("access_token")
            if not access_token:
                raise ValueError("Facebook connector missing access_token")
            return FacebookIntegration(access_token=access_token)
        
        elif connector.connector_type == ConnectorType.INSTAGRAM:
            access_token = config.get("access_token")
            instagram_account_id = config.get("instagram_account_id")
            if not access_token:
                raise ValueError("Instagram connector missing access_token")
            return InstagramIntegration(
                access_token=access_token,
                instagram_account_id=instagram_account_id
            )
        
        elif connector.connector_type == ConnectorType.TWITTER:
            # Twitter can use bearer token or OAuth tokens
            bearer_token = config.get("bearer_token")
            access_token = config.get("access_token")
            access_token_secret = config.get("access_token_secret")
            
            if bearer_token:
                # Use bearer token as access_token (TwitterIntegration uses Bearer auth)
                return TwitterIntegration(access_token=bearer_token)
            elif access_token:
                return TwitterIntegration(
                    access_token=access_token,
                    access_token_secret=access_token_secret
                )
            else:
                raise ValueError("Twitter connector missing authentication tokens")
        
        elif connector.connector_type == ConnectorType.LINKEDIN:
            access_token = config.get("access_token")
            if not access_token:
                raise ValueError("LinkedIn connector missing access_token")
            return LinkedInIntegration(access_token=access_token)
        
        elif connector.connector_type == ConnectorType.YOUTUBE:
            access_token = config.get("access_token")
            refresh_token = config.get("refresh_token")
            if not access_token:
                raise ValueError("YouTube connector missing access_token")
            return YouTubeIntegration(
                access_token=access_token,
                refresh_token=refresh_token
            )
        
        elif connector.connector_type == ConnectorType.TIKTOK:
            access_token = config.get("access_token")
            advertiser_id = config.get("advertiser_id")
            if not access_token:
                raise ValueError("TikTok connector missing access_token")
            return TikTokIntegration(
                access_token=access_token,
                advertiser_id=advertiser_id
            )
        
        else:
            raise ValueError(f"Unsupported connector type: {connector.connector_type.value}")
    
    @staticmethod
    def get_connector_for_social_account(
        db: Session,
        social_account_id: str,
    ) -> Optional[str]:
        """
        Get connector ID associated with a social account.
        This links social_accounts to connectors.
        
        Args:
            db: Database session
            social_account_id: Social account ID
            
        Returns:
            Connector ID if found
        """
        from app.db.models.social_account import SocialAccount
        
        social_account = db.query(SocialAccount).filter(
            SocialAccount.id == social_account_id
        ).first()
        
        if not social_account:
            return None
        
        # Find connector by platform and tenant
        from app.db.models.connector import Connector
        
        connector = db.query(Connector).filter(
            Connector.tenant_id == social_account.tenant_id,
            Connector.connector_type == social_account.platform.value,
            Connector.status == "ACTIVE"
        ).first()
        
        return connector.id if connector else None
