"""
Authentication and authorization dependencies for FastAPI endpoints.
"""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from typing import Optional

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.config.settings import settings
from app.middleware.request_context import get_context
from app.config.constants import CTX_USER_ID, CTX_TENANT_ID, CTX_ROLE

# Use standard HTTPBearer for authentication
# Swagger UI will show "Bearer Token" field - user enters just the token, we handle "Bearer " prefix
security = HTTPBearer(auto_error=False)

def get_access_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[str]:
    """
    Get token from Authorization header.
    Accepts both "Bearer <token>" format and just "<token>" for Swagger UI convenience.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    # If token already has "Bearer " prefix (shouldn't happen with HTTPBearer, but handle it)
    if token.startswith("Bearer "):
        return token[7:]
    return token


def get_current_user(
    token_value: Optional[str] = Depends(get_access_token),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token.
    Validates user is authenticated and active.
    Raises 401 if token is invalid or user not found.
    """
    
    if not token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required. Click 'Authorize' button and enter your token (just the token, no 'Bearer' prefix). Get token from /api/auth/login",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = token_value  # Already cleaned by get_access_token
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials: missing user ID in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User not found with ID: {user_id}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_optional(
    token_value: Optional[str] = Depends(get_access_token),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    Used for endpoints that work with or without authentication.
    """
    if not token_value:
        return None
    
    try:
        return get_current_user(token_value, db)
    except HTTPException:
        return None


def require_project(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    project_id: Optional[str] = None,
) -> Project:
    """
    Require that the user has at least one project.
    If project_id is provided, verify the user has access to it.
    Returns the project or raises 403 if no project exists.
    """
    tenant_id = current_user.tenant_id
    
    # If project_id is provided, verify it belongs to the user's tenant
    if project_id:
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.tenant_id == tenant_id,
            Project.is_active == True
        ).first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or you don't have access to it"
            )
        
        return project
    
    # Otherwise, check if user has any project
    project = db.query(Project).filter(
        Project.tenant_id == tenant_id,
        Project.is_active == True
    ).first()
    
    if not project:
        # Auto-create a default project for the user
        default_project = Project(
            tenant_id=tenant_id,
            name=f"{current_user.name}'s Project",
            description="Default project",
            created_by=current_user.id,
        )
        db.add(default_project)
        db.commit()
        db.refresh(default_project)
        return default_project
    
    return project


def get_current_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    """
    Get a specific project by ID, ensuring it belongs to the user's tenant.
    """
    tenant_id = current_user.tenant_id
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.tenant_id == tenant_id,
        Project.is_active == True
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or you don't have access to it"
        )
    
    return project
