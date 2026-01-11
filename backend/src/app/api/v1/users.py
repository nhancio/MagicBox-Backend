"""
Users API endpoints - manage user accounts.
Requires authentication for most operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.role import Role
from app.db.models.tenant import Tenant
from app.schemas.user import UserCreate, UserRead
from app.config.constants import ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user

router = APIRouter(tags=["Users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new user.
    Requires authentication and ADMIN or OWNER role.
    Regular users should use /api/auth/register.
    """
    # Only ADMIN and OWNER can create users
    if current_user.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN and OWNER roles can create users"
        )
    existing_user = (
        db.query(User)
        .filter(User.email == user_in.email)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Normalize role to uppercase (roles are stored in uppercase)
    normalized_role = user_in.role.upper()
    
    # Validate that the role exists in the roles table
    role = db.query(Role).filter(Role.name == normalized_role).first()
    if not role:
        # Get available roles from database for better error message
        available_roles = [r.name for r in db.query(Role).all()]
        if not available_roles:
            # If no roles in DB, show expected roles from constants
            available_roles = [ROLE_OWNER, ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER]
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: '{user_in.role}'. Available roles: {', '.join(available_roles)}"
        )

    # Handle tenant_id - use current user's tenant if not provided
    if user_in.tenant_id is None or user_in.tenant_id == 0 or user_in.tenant_id == "0":
        # Use the current user's tenant (admin creating user in same tenant)
        tenant_id_str = current_user.tenant_id
    else:
        # Convert tenant_id to string (tenant.id is String/UUID in the model)
        tenant_id_str = str(user_in.tenant_id)
        
        # Verify tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id_str).first()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # ADMIN can only create users in their own tenant
        if current_user.role == "ADMIN" and tenant_id_str != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="ADMIN can only create users in their own tenant"
            )

    user = User(
        email=user_in.email,
        name=user_in.name,
        password_hash=AuthService._hash_password(user_in.password),
        auth_provider="local",
        provider_id=user_in.email,
        tenant_id=tenant_id_str,
        role=normalized_role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserRead)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current authenticated user's information. Requires authentication.
    
    Use this endpoint to test if your token is working correctly.
    If this works, your token is valid and you can use other endpoints.
    """
    return current_user


@router.get("/{email}", response_model=UserRead)
def get_user_by_email(
    email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a user by email. Requires authentication."""
    # Users can only view their own profile or must be admin/owner
    if current_user.email != email and current_user.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this user"
        )
    
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
