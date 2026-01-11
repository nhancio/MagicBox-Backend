"""
OAuthState model - stores short-lived OAuth state for secure callback handling.
"""

from sqlalchemy import Column, String, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime, timedelta
import uuid


class OAuthState(Base):
    __tablename__ = "oauth_states"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True, index=True)

    provider = Column(String, nullable=False, index=True)  # meta/linkedin/google/twitter
    return_to = Column(String, nullable=True)  # frontend URL to redirect after success

    # For PKCE
    code_verifier = Column(String, nullable=True)

    extra_metadata = Column(JSON, nullable=True)

    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10), nullable=False, index=True)

    tenant = relationship("Tenant", back_populates="oauth_states")

