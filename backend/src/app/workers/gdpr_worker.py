"""
GDPR Worker - Background tasks for GDPR compliance (data deletion, export).
"""
from app.celery_app import celery_app
from app.db.session import SessionLocal
from app.db.models.user import User
from app.db.models.conversation import Conversation
from app.db.models.artifact import Artifact


@celery_app.task(name="gdpr.delete_user_data")
def delete_user_data_task(user_id: str):
    """Delete all user data for GDPR compliance."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Delete user's conversations
        conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
        for conv in conversations:
            db.delete(conv)
        
        # Delete user's artifacts
        artifacts = db.query(Artifact).filter(Artifact.user_id == user_id).all()
        for artifact in artifacts:
            db.delete(artifact)
        
        # Anonymize or delete user
        user.email = f"deleted_{user.id}@deleted.local"
        user.name = "Deleted User"
        
        db.commit()
        return {"success": True, "user_id": user_id}
    finally:
        db.close()


@celery_app.task(name="gdpr.export_user_data")
def export_user_data_task(user_id: str):
    """Export all user data for GDPR compliance."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        # Collect all user data
        conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
        artifacts = db.query(Artifact).filter(Artifact.user_id == user_id).all()
        
        # In production, would serialize and export to file/storage
        export_data = {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
            },
            "conversations": [{"id": c.id, "title": c.title} for c in conversations],
            "artifacts": [{"id": a.id, "title": a.title} for a in artifacts],
        }
        
        return {"success": True, "data": export_data}
    finally:
        db.close()
