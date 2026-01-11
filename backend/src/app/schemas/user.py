from pydantic import BaseModel, EmailStr, Field
from typing import Union, Optional

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email address", example="editor@example.com")
    name: str = Field(..., description="User full name", example="Editor User")
    password: str = Field(..., description="User password", example="password123")
    tenant_id: Optional[Union[str, int]] = Field(None, description="Tenant ID (optional - uses current user's tenant if not provided)", example=None)
    role: str = Field(..., description="User role", example="EDITOR")


class UserRead(BaseModel):
    id: str = Field(..., description="User ID (UUID)", example="550e8400-e29b-41d4-a716-446655440000")
    email: EmailStr = Field(..., description="User email address", example="user@example.com")
    name: str = Field(..., description="User full name", example="John Doe")
    tenant_id: str = Field(..., description="Tenant ID (UUID)", example="660e8400-e29b-41d4-a716-446655440000")
    role: str = Field(..., description="User role", example="OWNER")

    class Config:
        from_attributes = True
