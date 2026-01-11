"""
Audit Service - Logs security and compliance events.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.activity_timeline import ActivityTimeline, ActivityType
from app.middleware.request_context import get_context
from app.config.constants import CTX_TENANT_ID, CTX_USER_ID
from app.utils.time import utc_now
import uuid


class AuditService:
    """Service for audit logging."""
    
    @staticmethod
    def log_activity(
        db: Session,
        activity_type: ActivityType,
        description: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> ActivityTimeline:
        """Log an activity."""
        tenant_id = tenant_id or get_context(CTX_TENANT_ID)
        user_id = user_id or get_context(CTX_USER_ID)
        
        activity = ActivityTimeline(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            extra_metadata=metadata,
        )
        
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity
    
    @staticmethod
    def log_login(db: Session, user_id: str, success: bool = True):
        """Log login attempt."""
        return AuditService.log_activity(
            db=db,
            activity_type=ActivityType.USER_LOGIN if success else ActivityType.USER_LOGIN_FAILED,
            description=f"User login {'successful' if success else 'failed'}",
            user_id=user_id,
        )
    
    @staticmethod
    def log_data_access(
        db: Session,
        entity_type: str,
        entity_id: str,
        action: str,
    ):
        """Log data access."""
        return AuditService.log_activity(
            db=db,
            activity_type=ActivityType.DATA_ACCESS,
            description=f"{action} {entity_type} {entity_id}",
            entity_type=entity_type,
            entity_id=entity_id,
            metadata={"action": action},
        )
