# Connector Configuration System

## Overview

The connector system allows users to configure and manage integrations with different social media platforms. Each connector type has its own configuration schema with platform-specific credentials.

## Architecture

### Models

- **`Connector`** (`db/models/connector.py`): Stores connector configurations
  - `connector_type`: Platform type (FACEBOOK, INSTAGRAM, TWITTER, etc.)
  - `config`: Platform-specific configuration (JSON, encrypted)
  - `status`: ACTIVE, INACTIVE, ERROR, PENDING_SETUP
  - `last_verified_at`: Last time credentials were verified

### Schemas

- **`ConnectorCreate`**: Create connector request
- **`ConnectorUpdate`**: Update connector request
- **`ConnectorRead`**: Connector response (sanitized)
- **Platform-specific configs**:
  - `FacebookConnectorConfig`
  - `InstagramConnectorConfig`
  - `TwitterConnectorConfig`
  - `LinkedInConnectorConfig`
  - `YouTubeConnectorConfig`
  - `TikTokConnectorConfig`

### Services

- **`ConnectorService`**: Manages connector CRUD operations
  - Validates configurations against platform schemas
  - Encrypts sensitive fields (secrets, tokens)
  - Verifies connector credentials
  - Sanitizes configs for API responses

- **`IntegrationFactory`**: Creates integration instances from connectors
  - Gets decrypted config from connector
  - Instantiates appropriate integration class
  - Links connectors to social accounts

## API Endpoints

### `/api/connectors`

- `POST /api/connectors/` - Create connector
- `GET /api/connectors/` - List connectors (filterable by type/status)
- `GET /api/connectors/{id}` - Get connector details
- `GET /api/connectors/{id}/config` - Get sanitized config (secrets masked)
- `PATCH /api/connectors/{id}` - Update connector
- `DELETE /api/connectors/{id}` - Delete connector
- `POST /api/connectors/{id}/verify` - Verify connector credentials
- `GET /api/connectors/types/{type}/schema` - Get config schema for connector type

## Configuration Schemas

### Facebook
```json
{
  "app_id": "string",
  "app_secret": "string",
  "access_token": "string (optional)",
  "refresh_token": "string (optional)",
  "page_id": "string (optional)",
  "verify_token": "string (optional)"
}
```

### Instagram
```json
{
  "client_id": "string",
  "client_secret": "string",
  "access_token": "string (optional)",
  "refresh_token": "string (optional)",
  "instagram_account_id": "string (optional)",
  "facebook_page_id": "string (optional)"
}
```

### Twitter
```json
{
  "api_key": "string",
  "api_secret": "string",
  "bearer_token": "string (optional)",
  "access_token": "string (optional)",
  "access_token_secret": "string (optional)",
  "client_id": "string (optional)",
  "client_secret": "string (optional)"
}
```

### LinkedIn
```json
{
  "client_id": "string",
  "client_secret": "string",
  "access_token": "string (optional)",
  "refresh_token": "string (optional)",
  "organization_id": "string (optional)"
}
```

### YouTube
```json
{
  "client_id": "string",
  "client_secret": "string",
  "access_token": "string (optional)",
  "refresh_token": "string (optional)",
  "channel_id": "string (optional)",
  "api_key": "string (optional)"
}
```

### TikTok
```json
{
  "client_key": "string",
  "client_secret": "string",
  "access_token": "string (optional)",
  "refresh_token": "string (optional)",
  "advertiser_id": "string (optional)"
}
```

## Usage Examples

### Create a Facebook Connector

```python
POST /api/connectors/
{
  "name": "My Facebook Page",
  "connector_type": "FACEBOOK",
  "config": {
    "app_id": "123456789",
    "app_secret": "secret123",
    "access_token": "token123",
    "page_id": "page123"
  }
}
```

### Verify Connector

```python
POST /api/connectors/{id}/verify
# Tests API connection and updates status
```

### Use Connector in Integration

```python
from app.services.integration_factory import IntegrationFactory

# Get integration instance from connector
integration = IntegrationFactory.create_integration(db, connector_id)

# Use integration
result = integration.publish_post(content="Hello World!")
```

## Security

- **Encryption**: Sensitive fields (secrets, tokens) are encrypted using `EncryptionService`
- **Sanitization**: API responses mask secrets (show only first/last 4 chars)
- **Validation**: Configs are validated against Pydantic schemas
- **Verification**: Connectors can be verified to test API connectivity

## Integration with Social Accounts

Connectors are separate from `SocialAccount` records:
- **Connector**: Platform configuration (credentials, API keys)
- **SocialAccount**: User's connected account (OAuth tokens, account info)

A connector can be used by multiple social accounts of the same platform within a tenant.
