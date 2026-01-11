from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserRead


# ---------- Requests ----------

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address", example="user@example.com")
    name: str = Field(..., description="User full name", example="John Doe")
    password: str = Field(..., description="User password", example="password123")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address", example="user@example.com")
    password: str = Field(..., description="User password", example="password123")


class GoogleLoginRequest(BaseModel):
    id_token: str


# ---------- Responses ----------

class AuthResponse(BaseModel):
    access_token: str
    user: UserRead
