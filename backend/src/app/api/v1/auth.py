from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.auth_service import AuthService
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    GoogleLoginRequest,
    AuthResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        return AuthService.register(
            db,
            email=payload.email,
            name=payload.name,
            password=payload.password,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        return AuthService.login(db, payload.email, payload.password)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/google", response_model=AuthResponse)
async def google_login(
    payload: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    try:
        return await AuthService.login_with_google(db, payload.id_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
