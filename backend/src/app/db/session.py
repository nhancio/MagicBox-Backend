from app.db.database import SessionLocal
from app.db.models import User, Role, Tenant  # noqa


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
