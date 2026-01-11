from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta
import bcrypt

from app.db.models.user import User
from app.db.models.tenant import Tenant
from app.db.models.project import Project
from app.integrations.google_oauth import verify_google_token
from app.config.settings import settings

JWT_EXP_MINUTES = 60 * 24  # 1 day


class AuthService:

    # ---------- Public APIs ----------

    @staticmethod
    def register(db: Session, email: str, name: str, password: str) -> dict:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("User already exists")

        tenant = Tenant(name=f"{name}'s workspace")
        db.add(tenant)
        db.flush()

        user = User(
            email=email,
            name=name,
            auth_provider="local",
            password_hash=AuthService._hash_password(password),
            tenant_id=tenant.id,
            role="OWNER",
        )

        db.add(user)
        db.flush()  # Flush to get user.id
        
        # Auto-create a default project for the user
        default_project = Project(
            tenant_id=tenant.id,
            name=f"{name}'s Project",
            description="Default project",
            created_by=user.id,
        )
        db.add(default_project)
        db.commit()

        return AuthService._auth_response(user)

    @staticmethod
    def login(db: Session, email: str, password: str) -> dict:
        user = db.query(User).filter(User.email == email).first()

        if not user or user.auth_provider != "local":
            raise ValueError("Invalid credentials")

        if not AuthService._verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
        
        # Ensure user has at least one project
        from app.db.models.project import Project
        project = db.query(Project).filter(
            Project.tenant_id == user.tenant_id,
            Project.is_active == True
        ).first()
        
        if not project:
            # Auto-create a default project for existing users
            default_project = Project(
                tenant_id=user.tenant_id,
                name=f"{user.name}'s Project",
                description="Default project",
                created_by=user.id,
            )
            db.add(default_project)
            db.commit()

        return AuthService._auth_response(user)

    @staticmethod
    async def login_with_google(db: Session, id_token: str) -> dict:
        google_user = await verify_google_token(id_token)

        user = db.query(User).filter(User.email == google_user["email"]).first()

        if not user:
            tenant = Tenant(name=f"{google_user['email']}'s workspace")
            db.add(tenant)
            db.flush()

            user = User(
                email=google_user["email"],
                name=google_user["name"],
                auth_provider="google",
                provider_id=google_user["provider_id"],
                tenant_id=tenant.id,
                role="OWNER",
            )
            db.add(user)
            db.flush()  # Flush to get user.id
            
            # Auto-create a default project for the user
            default_project = Project(
                tenant_id=tenant.id,
                name=f"{google_user['name']}'s Project",
                description="Default project",
                created_by=user.id,
            )
            db.add(default_project)
            db.commit()

        return AuthService._auth_response(user)

    # ---------- Helpers ----------

    @staticmethod
    def _auth_response(user: User) -> dict:
        token = AuthService._generate_jwt(user)
        return {
            "access_token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "tenant_id": user.tenant_id,
                "role": user.role,
            },
        }

    @staticmethod
    def _generate_jwt(user: User) -> str:
        payload = {
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "role": user.role,
            "exp": datetime.utcnow() + timedelta(minutes=JWT_EXP_MINUTES),
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def _verify_password(password: str, hashed: str) -> bool:
        """Verify a password against a bcrypt hash."""
        try:
            password_bytes = password.encode('utf-8')
            hash_bytes = hashed.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception:
            return False
