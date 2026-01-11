"""
Connector Service - Manages connector configurations and validation.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.models.connector import Connector, ConnectorType, ConnectorStatus
from app.schemas.connector import (
    ConnectorCreate,
    ConnectorUpdate,
    FacebookConnectorConfig,
    InstagramConnectorConfig,
    TwitterConnectorConfig,
    LinkedInConnectorConfig,
    YouTubeConnectorConfig,
    TikTokConnectorConfig,
)
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID
from app.utils.errors import ValidationError
from app.security.encryption import EncryptionService
import uuid


class ConnectorService:
    """Service for managing connector configurations."""
    
    # Connector config validators for each type
    CONFIG_VALIDATORS = {
        ConnectorType.FACEBOOK: FacebookConnectorConfig,
        ConnectorType.INSTAGRAM: InstagramConnectorConfig,
        ConnectorType.TWITTER: TwitterConnectorConfig,
        ConnectorType.LINKEDIN: LinkedInConnectorConfig,
        ConnectorType.YOUTUBE: YouTubeConnectorConfig,
        ConnectorType.TIKTOK: TikTokConnectorConfig,
    }
    
    @staticmethod
    def validate_config(connector_type: ConnectorType, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate connector configuration against platform-specific schema.
        
        Args:
            connector_type: Type of connector
            config: Configuration dictionary
            
        Returns:
            Validated and normalized config
            
        Raises:
            ValidationError: If config is invalid
        """
        validator_class = ConnectorService.CONFIG_VALIDATORS.get(connector_type)
        if not validator_class:
            # For OTHER type, just return as-is
            return config
        
        try:
            # Validate config
            validated = validator_class(**config)
            
            # Convert back to dict and encrypt sensitive fields
            config_dict = validated.model_dump(exclude_none=True)
            
            # Encrypt sensitive fields
            sensitive_fields = ['app_secret', 'client_secret', 'api_secret', 'access_token', 'refresh_token', 'bearer_token', 'access_token_secret']
            for field in sensitive_fields:
                if field in config_dict and config_dict[field]:
                    config_dict[field] = EncryptionService.encrypt(config_dict[field])
            
            return config_dict
        except Exception as e:
            raise ValidationError(f"Invalid configuration for {connector_type.value}: {str(e)}")
    
    @staticmethod
    def decrypt_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in config."""
        decrypted = config.copy()
        sensitive_fields = ['app_secret', 'client_secret', 'api_secret', 'access_token', 'refresh_token', 'bearer_token', 'access_token_secret']
        
        for field in sensitive_fields:
            if field in decrypted and decrypted[field]:
                try:
                    decrypted[field] = EncryptionService.decrypt(decrypted[field])
                except Exception:
                    # If decryption fails, keep encrypted value
                    pass
        
        return decrypted
    
    @staticmethod
    def sanitize_config_for_response(config: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize config for API response (mask secrets)."""
        sanitized = config.copy()
        sensitive_fields = ['app_secret', 'client_secret', 'api_secret', 'access_token', 'refresh_token', 'bearer_token', 'access_token_secret']
        
        for field in sensitive_fields:
            if field in sanitized and sanitized[field]:
                value = sanitized[field]
                if isinstance(value, str) and len(value) > 8:
                    sanitized[field] = value[:4] + "***" + value[-4:]
                else:
                    sanitized[field] = "***"
        
        return sanitized
    
    @staticmethod
    def create_connector(db: Session, connector_data: ConnectorCreate) -> Connector:
        """Create a new connector."""
        tenant_id = get_context(CTX_TENANT_ID)
        user_id = get_context(CTX_USER_ID)
        
        if not tenant_id or not user_id:
            raise ValueError("Tenant ID and User ID must be in request context")
        
        # Validate configuration
        validated_config = ConnectorService.validate_config(
            connector_data.connector_type,
            connector_data.config
        )
        
        # Create connector
        connector = Connector(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            name=connector_data.name,
            connector_type=connector_data.connector_type,
            config=validated_config,
            status=ConnectorStatus.PENDING_SETUP,
            extra_metadata=connector_data.extra_metadata,
        )
        
        db.add(connector)
        db.commit()
        db.refresh(connector)
        return connector
    
    @staticmethod
    def get_connector(db: Session, connector_id: str) -> Optional[Connector]:
        """Get connector by ID."""
        tenant_id = get_context(CTX_TENANT_ID)
        
        return db.query(Connector).filter(
            Connector.id == connector_id,
            Connector.tenant_id == tenant_id
        ).first()
    
    @staticmethod
    def list_connectors(
        db: Session,
        connector_type: Optional[ConnectorType] = None,
        status: Optional[ConnectorStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Connector]:
        """List connectors for tenant."""
        tenant_id = get_context(CTX_TENANT_ID)
        
        query = db.query(Connector).filter(Connector.tenant_id == tenant_id)
        
        if connector_type:
            query = query.filter(Connector.connector_type == connector_type)
        if status:
            query = query.filter(Connector.status == status)
        
        return query.order_by(Connector.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_connector(
        db: Session,
        connector_id: str,
        connector_data: ConnectorUpdate,
    ) -> Optional[Connector]:
        """Update connector."""
        connector = ConnectorService.get_connector(db, connector_id)
        if not connector:
            return None
        
        # Update fields
        if connector_data.name is not None:
            connector.name = connector_data.name
        if connector_data.status is not None:
            connector.status = connector_data.status
        if connector_data.extra_metadata is not None:
            connector.extra_metadata = connector_data.extra_metadata
        
        # Update config if provided
        if connector_data.config is not None:
            validated_config = ConnectorService.validate_config(
                connector.connector_type,
                connector_data.config
            )
            connector.config = validated_config
        
        db.commit()
        db.refresh(connector)
        return connector
    
    @staticmethod
    def delete_connector(db: Session, connector_id: str) -> bool:
        """Delete connector."""
        connector = ConnectorService.get_connector(db, connector_id)
        if not connector:
            return False
        
        db.delete(connector)
        db.commit()
        return True
    
    @staticmethod
    def verify_connector(db: Session, connector_id: str) -> Dict[str, Any]:
        """
        Verify connector credentials by testing API connection.
        
        Returns:
            Dict with verification result
        """
        connector = ConnectorService.get_connector(db, connector_id)
        if not connector:
            raise ValueError("Connector not found")
        
        try:
            # Decrypt config
            decrypted_config = ConnectorService.decrypt_config(connector.config)
            
            # Test connection based on connector type
            is_valid = ConnectorService._test_connection(connector.connector_type, decrypted_config)
            
            if is_valid:
                connector.status = ConnectorStatus.ACTIVE
                connector.last_verified_at = datetime.utcnow()
                connector.last_error = None
            else:
                connector.status = ConnectorStatus.ERROR
                connector.last_error = "Connection test failed"
            
            db.commit()
            
            return {
                "success": is_valid,
                "status": connector.status.value,
                "last_verified_at": connector.last_verified_at.isoformat() if connector.last_verified_at else None,
            }
        except Exception as e:
            connector.status = ConnectorStatus.ERROR
            connector.last_error = str(e)
            db.commit()
            return {
                "success": False,
                "status": ConnectorStatus.ERROR.value,
                "error": str(e),
            }
    
    @staticmethod
    def _test_connection(connector_type: ConnectorType, config: Dict[str, Any]) -> bool:
        """Test connection to platform API."""
        import httpx
        
        try:
            if connector_type == ConnectorType.FACEBOOK:
                # Test Facebook Graph API
                access_token = config.get("access_token")
                if not access_token:
                    return False
                response = httpx.get(
                    f"https://graph.facebook.com/v18.0/me",
                    params={"access_token": access_token},
                    timeout=5.0
                )
                return response.status_code == 200
            
            elif connector_type == ConnectorType.INSTAGRAM:
                # Test Instagram Graph API
                access_token = config.get("access_token")
                if not access_token:
                    return False
                response = httpx.get(
                    f"https://graph.facebook.com/v18.0/me",
                    params={"access_token": access_token},
                    timeout=5.0
                )
                return response.status_code == 200
            
            elif connector_type == ConnectorType.TWITTER:
                # Test Twitter API
                bearer_token = config.get("bearer_token") or config.get("access_token")
                if not bearer_token:
                    return False
                response = httpx.get(
                    "https://api.twitter.com/2/users/me",
                    headers={"Authorization": f"Bearer {bearer_token}"},
                    timeout=5.0
                )
                return response.status_code == 200
            
            elif connector_type == ConnectorType.LINKEDIN:
                # Test LinkedIn API
                access_token = config.get("access_token")
                if not access_token:
                    return False
                response = httpx.get(
                    "https://api.linkedin.com/v2/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=5.0
                )
                return response.status_code == 200
            
            elif connector_type == ConnectorType.YOUTUBE:
                # Test YouTube API
                access_token = config.get("access_token")
                if not access_token:
                    return False
                response = httpx.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "snippet", "mine": "true"},
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=5.0
                )
                return response.status_code == 200
            
            elif connector_type == ConnectorType.TIKTOK:
                # Test TikTok API (if available)
                access_token = config.get("access_token")
                if not access_token:
                    return False
                # TikTok API endpoint would go here
                return True
            
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_connector_config_for_integration(db: Session, connector_id: str) -> Dict[str, Any]:
        """Get decrypted connector config for use in integrations."""
        connector = ConnectorService.get_connector(db, connector_id)
        if not connector:
            raise ValueError("Connector not found")
        
        return ConnectorService.decrypt_config(connector.config)
