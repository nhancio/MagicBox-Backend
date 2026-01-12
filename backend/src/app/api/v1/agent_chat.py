"""
Agent Chat API - Conversational interface for interacting with agents.
Enables natural language chat with Image and Reel agents.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.db.models.agent import Agent
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/projects/{project_id}/agents/{agent_id}/chat", tags=["Agent Chat"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., description="User's message to the agent")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (creates new if not provided)")


class ChatMessageResponse(BaseModel):
    success: bool
    response: str
    conversation_id: str
    message_id: str
    run_id: Optional[str] = None
    artifact_id: Optional[str] = None
    metadata: dict = {}


@router.post("/message", response_model=ChatMessageResponse, status_code=status.HTTP_200_OK)
def send_agent_message(
    project_id: str,
    agent_id: str,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Send a message to an agent and get a conversational response.
    
    This endpoint handles natural language conversations with agents.
    Agents will generate content (images, reels, posts) based on the conversation.
    """
    try:
        # Verify project_id matches
        if project_id != current_project.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project ID mismatch"
            )
        
        # Get agent
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # Get agent class based on agent name
        agent_instance = _get_agent_instance(agent, db, request.conversation_id)
        
        if not agent_instance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent '{agent.name}' is not a conversational agent"
            )
        
        # Send message and get response
        result = agent_instance.send_message(
            user_message=request.message,
            user_id=current_user.id,
            project_id=project_id,
            attachments=None,  # TODO: Support file attachments
        )
        
        return ChatMessageResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/conversations", status_code=status.HTTP_200_OK)
def list_agent_conversations(
    project_id: str,
    agent_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    """List all conversations for this agent in the current project."""
    from app.db.models.conversation import Conversation
    
    # Verify project_id matches
    if project_id != current_project.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID mismatch"
        )
    
    # Get conversations for this agent and project
    conversations = db.query(Conversation).filter(
        Conversation.project_id == project_id,
        Conversation.agent_id == agent_id,
        Conversation.user_id == current_user.id,
        Conversation.is_archived == False,
    ).order_by(Conversation.last_message_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "success": True,
        "conversations": [
            {
                "id": conv.id,
                "title": conv.title or "New Conversation",
                "created_at": conv.created_at.isoformat() if conv.created_at else None,
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                "message_count": _get_message_count(db, conv.id),
            }
            for conv in conversations
        ],
        "total": len(conversations),
    }


@router.get("/conversations/{conversation_id}/messages", status_code=status.HTTP_200_OK)
def get_conversation_messages(
    project_id: str,
    agent_id: str,
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Get all messages in a conversation."""
    from app.db.models.conversation import Conversation, ConversationMessage
    
    # Verify conversation belongs to user and agent
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.project_id == project_id,
        Conversation.agent_id == agent_id,
        Conversation.user_id == current_user.id,
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation_id
    ).order_by(ConversationMessage.created_at.asc()).all()
    
    return {
        "success": True,
        "conversation_id": conversation_id,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "run_id": msg.run_id,
            }
            for msg in messages
        ],
    }


def _get_agent_instance(agent: Agent, db: Session, conversation_id: Optional[str]):
    """Get the appropriate agent instance based on agent name."""
    from app.ai.agents.image_chat_agent import ImageChatAgent
    from app.ai.agents.reel_chat_agent import ReelChatAgent
    
    agent_name_lower = agent.name.lower()
    
    if "image" in agent_name_lower:
        return ImageChatAgent(db, agent, conversation_id)
    elif "reel" in agent_name_lower or "short" in agent_name_lower:
        return ReelChatAgent(db, agent, conversation_id)
    else:
        # Try to use base conversational agent
        from app.ai.agents.conversational_agent import ConversationalAgent
        return ConversationalAgent(db, agent, conversation_id)


def _get_message_count(db: Session, conversation_id: str) -> int:
    """Get message count for a conversation."""
    from app.db.models.conversation import ConversationMessage
    return db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation_id
    ).count()
