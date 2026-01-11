"""
Connector schemas - Pydantic models for connector configuration.
Each connector type has its own configuration schema.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.db.models.connector import ConnectorType, ConnectorStatus


# Base connector config schemas for each platform
class FacebookConnectorConfig(BaseModel):
    """Facebook connector configuration."""
    app_id: str = Field(..., description="Facebook App ID")
    app_secret: str = Field(..., description="Facebook App Secret")
    access_token: Optional[str] = Field(None, description="Access token (if using manual setup)")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    page_id: Optional[str] = Field(None, description="Default Facebook Page ID")
    verify_token: Optional[str] = Field(None, description="Webhook verify token")


class InstagramConnectorConfig(BaseModel):
    """Instagram connector configuration."""
    client_id: str = Field(..., description="Instagram Client ID")
    client_secret: str = Field(..., description="Instagram Client Secret")
    access_token: Optional[str] = Field(None, description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    instagram_account_id: Optional[str] = Field(None, description="Instagram Business Account ID")
    facebook_page_id: Optional[str] = Field(None, description="Associated Facebook Page ID")


class TwitterConnectorConfig(BaseModel):
    """Twitter/X connector configuration."""
    api_key: str = Field(..., description="Twitter API Key")
    api_secret: str = Field(..., description="Twitter API Secret")
    bearer_token: Optional[str] = Field(None, description="Bearer token (for app-only auth)")
    access_token: Optional[str] = Field(None, description="OAuth access token")
    access_token_secret: Optional[str] = Field(None, description="OAuth access token secret")
    client_id: Optional[str] = Field(None, description="OAuth 2.0 Client ID")
    client_secret: Optional[str] = Field(None, description="OAuth 2.0 Client Secret")


class LinkedInConnectorConfig(BaseModel):
    """LinkedIn connector configuration."""
    client_id: str = Field(..., description="LinkedIn Client ID")
    client_secret: str = Field(..., description="LinkedIn Client Secret")
    access_token: Optional[str] = Field(None, description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    organization_id: Optional[str] = Field(None, description="LinkedIn Organization ID (for company pages)")


class YouTubeConnectorConfig(BaseModel):
    """YouTube connector configuration."""
    client_id: str = Field(..., description="YouTube OAuth Client ID")
    client_secret: str = Field(..., description="YouTube OAuth Client Secret")
    access_token: Optional[str] = Field(None, description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    channel_id: Optional[str] = Field(None, description="YouTube Channel ID")
    api_key: Optional[str] = Field(None, description="YouTube Data API Key (for public data)")


class TikTokConnectorConfig(BaseModel):
    """TikTok connector configuration."""
    client_key: str = Field(..., description="TikTok Client Key")
    client_secret: str = Field(..., description="TikTok Client Secret")
    access_token: Optional[str] = Field(None, description="Access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    advertiser_id: Optional[str] = Field(None, description="TikTok Advertiser ID")


class OtherConnectorConfig(BaseModel):
    """Generic connector configuration for other platforms."""
    config: Dict[str, Any] = Field(..., description="Platform-specific configuration")


# Connector request/response schemas
class ConnectorCreate(BaseModel):
    """Create connector request."""
    name: str = Field(..., description="Connector name")
    connector_type: ConnectorType = Field(..., description="Connector type")
    config: Dict[str, Any] = Field(..., description="Connector configuration (platform-specific)")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ConnectorUpdate(BaseModel):
    """Update connector request."""
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[ConnectorStatus] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class ConnectorRead(BaseModel):
    """Connector response schema."""
    id: str
    name: str
    connector_type: ConnectorType
    status: ConnectorStatus
    is_active: bool
    last_verified_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConnectorConfigRead(BaseModel):
    """Connector configuration response (sanitized - no secrets)."""
    connector_type: ConnectorType
    config: Dict[str, Any]  # Secrets will be masked
    
    class Config:
        from_attributes = True
