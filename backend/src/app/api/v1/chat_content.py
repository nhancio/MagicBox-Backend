"""
Chat-based Content Generation API - Conversational interface for content creation.
Enables natural language requests like Syntagro.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.services.chat_content_service import ChatContentService
from app.services.credit_service import CreditService
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/chat", tags=["Chat Content"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="User's natural language request", example="I need a reel which promotes my brand truvelocity")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (creates new if not provided)")
    project_id: Optional[str] = Field(None, description="Project ID (uses current project if not provided)")


@router.post("/message", status_code=status.HTTP_200_OK)
def send_chat_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Send a chat message to generate content.
    Natural language requests like "I need a reel which promotes my brand..."
    
    Requires authentication and a project.
    Deducts credits based on content type generated.
    """
    from app.services.conversation_service import ConversationService
    from app.schemas.conversation import ConversationCreate
    
    try:
        # Check credits before generating
        if not CreditService.check_credits_available(db, "post_generation"):
            balance = CreditService.get_credit_balance(db)
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Insufficient credits. Current balance: {balance['balance']}. Please upgrade your plan."
            )
        
        # Get or create conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            # Create new conversation
            conversation_data = ConversationCreate(
                title=None,  # Will be auto-generated
                project_id=request.project_id or current_project.id,
            )
            conversation = ConversationService.create_conversation(db, conversation_data)
            conversation_id = conversation.id
        
        # Process message and generate content
        result = ChatContentService.process_content_request(
            db=db,
            conversation_id=conversation_id,
            user_message=request.message,
            project_id=request.project_id or current_project.id,
        )
        
        # Deduct credits based on content type
        operation = "post_generation"  # Default
        if result.get("content_type") == "reel":
            operation = "reel_generation"
        elif result.get("content_type") == "video":
            operation = "video_generation"
        elif result.get("content_type") == "story":
            operation = "story_generation"
        
        credit_result = CreditService.deduct_credits(db, operation)
        if not credit_result["success"]:
            # Rollback? Or just log warning
            pass
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "ai_response": result["ai_response"],
            "artifact": result["artifact"],
            "credits_used": credit_result.get("cost", 0),
            "remaining_credits": credit_result.get("new_balance"),
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Get all messages in a conversation."""
    from app.services.conversation_service import ConversationService
    
    conversation = ConversationService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = ConversationService.get_messages(db, conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ]
    }
