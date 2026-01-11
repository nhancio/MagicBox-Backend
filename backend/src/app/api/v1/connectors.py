"""
Connectors API endpoints - Manage connector configurations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.db.models.connector import ConnectorType, ConnectorStatus
from app.schemas.connector import (
    ConnectorCreate,
    ConnectorUpdate,
    ConnectorRead,
    ConnectorConfigRead,
)
from app.services.connector_service import ConnectorService
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/projects/{project_id}/connectors", tags=["Connectors"])


@router.post("/", response_model=ConnectorRead, status_code=status.HTTP_201_CREATED)
def create_connector(
    project_id: str,
    connector_data: ConnectorCreate,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Create a new connector configuration."""
    try:
        connector = ConnectorService.create_connector(db, connector_data)
        return connector
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ConnectorRead])
def list_connectors(
    project_id: str,
    connector_type: Optional[ConnectorType] = None,
    status: Optional[ConnectorStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """List all connectors for the current tenant."""
    connectors = ConnectorService.list_connectors(
        db=db,
        connector_type=connector_type,
        status=status,
        skip=skip,
        limit=limit,
    )
    return connectors


@router.get("/{connector_id}", response_model=ConnectorRead)
def get_connector(
    project_id: str,
    connector_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Get connector details."""
    connector = ConnectorService.get_connector(db, connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    return connector


@router.get("/{connector_id}/config", response_model=ConnectorConfigRead)
def get_connector_config(
    project_id: str,
    connector_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Get connector configuration (sanitized - secrets masked)."""
    connector = ConnectorService.get_connector(db, connector_id)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    
    sanitized_config = ConnectorService.sanitize_config_for_response(connector.config)
    
    return ConnectorConfigRead(
        connector_type=connector.connector_type,
        config=sanitized_config,
    )


@router.patch("/{connector_id}", response_model=ConnectorRead)
def update_connector(
    project_id: str,
    connector_id: str,
    connector_data: ConnectorUpdate,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Update connector configuration."""
    connector = ConnectorService.update_connector(db, connector_id, connector_data)
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )
    return connector


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connector(
    project_id: str,
    connector_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Delete connector."""
    success = ConnectorService.delete_connector(db, connector_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found"
        )


@router.post("/{connector_id}/verify", status_code=status.HTTP_200_OK)
def verify_connector(
    project_id: str,
    connector_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Verify connector credentials by testing API connection."""
    try:
        result = ConnectorService.verify_connector(db, connector_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/types/{connector_type}/schema", status_code=status.HTTP_200_OK)
def get_connector_schema(
    project_id: str,
    connector_type: ConnectorType,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
):
    """Get configuration schema for a connector type."""
    from app.schemas.connector import (
        FacebookConnectorConfig,
        InstagramConnectorConfig,
        TwitterConnectorConfig,
        LinkedInConnectorConfig,
        YouTubeConnectorConfig,
        TikTokConnectorConfig,
    )
    
    schema_map = {
        ConnectorType.FACEBOOK: FacebookConnectorConfig.model_json_schema(),
        ConnectorType.INSTAGRAM: InstagramConnectorConfig.model_json_schema(),
        ConnectorType.TWITTER: TwitterConnectorConfig.model_json_schema(),
        ConnectorType.LINKEDIN: LinkedInConnectorConfig.model_json_schema(),
        ConnectorType.YOUTUBE: YouTubeConnectorConfig.model_json_schema(),
        ConnectorType.TIKTOK: TikTokConnectorConfig.model_json_schema(),
    }
    
    schema = schema_map.get(connector_type)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found for connector type: {connector_type.value}"
        )
    
    return {
        "connector_type": connector_type.value,
        "schema": schema,
        "required_fields": list(schema.get("properties", {}).keys()),
    }
