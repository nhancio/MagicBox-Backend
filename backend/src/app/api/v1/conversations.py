"""
Conversations API endpoints - manage chat sessions with AI.
Requires authentication and an active project.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.services.conversation_service import ConversationService
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationRead,
    ConversationMessageCreate,
    ConversationMessageRead,
    ConversationWithMessages,
)
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Create a new conversation. Requires authentication and a project."""
    try:
        # Ensure conversation is associated with the current project if not specified
        if not conversation_data.project_id:
            conversation_data.project_id = current_project.id
        
        conversation = ConversationService.create_conversation(db, conversation_data)
        return conversation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ConversationRead])
def list_conversations(
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    project_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List conversations for the current tenant. Requires authentication and a project."""
    # Use current project if project_id not specified
    if not project_id:
        project_id = current_project.id
    
    conversations = ConversationService.list_conversations(
        db, project_id=project_id, skip=skip, limit=limit
    )
    return conversations


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Get a conversation by ID. Requires authentication and a project."""
    conversation = ConversationService.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation


@router.get("/{conversation_id}/messages", response_model=List[ConversationMessageRead])
def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get messages for a conversation. Requires authentication and a project."""
    messages = ConversationService.get_messages(db, conversation_id, skip=skip, limit=limit)
    return messages


@router.post("/{conversation_id}/messages", response_model=ConversationMessageRead, status_code=status.HTTP_201_CREATED)
def add_message(
    conversation_id: str,
    message_data: ConversationMessageCreate,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Add a message to a conversation. Requires authentication and a project."""
    try:
        message = ConversationService.add_message(db, conversation_id, message_data)
        return message
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{conversation_id}", response_model=ConversationRead)
def update_conversation(
    conversation_id: str,
    conversation_data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Update a conversation. Requires authentication and a project."""
    conversation = ConversationService.update_conversation(db, conversation_id, conversation_data)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return conversation


@router.post("/{conversation_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Archive a conversation. Requires authentication and a project."""
    success = ConversationService.archive_conversation(db, conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return None
