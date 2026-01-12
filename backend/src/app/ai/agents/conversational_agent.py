"""
Conversational Agent - Base class for chat-based agents.
Handles natural language conversations and context management.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.db.models.agent import Agent
from app.db.models.conversation import Conversation, ConversationMessage
from app.db.models.run import Run, RunStatus
from app.db.models.artifact import Artifact, ArtifactType, ArtifactStatus
from app.ai.agents.base_agent import BaseAgent
from app.services.ai_service import AIService
from app.services.ai_image_service import AIImageService
from app.services.ai_video_service import AIVideoService
from app.utils.time import utc_now
import json
import uuid


class ConversationalAgent(BaseAgent):
    """Base class for conversational agents that handle chat interactions."""
    
    def __init__(self, db: Session, agent: Agent, conversation_id: Optional[str] = None):
        super().__init__(db, agent, conversation_id)
        self.conversation_id = conversation_id
    
    def send_message(
        self,
        user_message: str,
        user_id: str,
        project_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a conversational response.
        
        Args:
            user_message: User's message
            user_id: User ID
            project_id: Project ID
            attachments: Optional file attachments
            
        Returns:
            Dict with assistant response and metadata
        """
        # Get or create conversation
        conversation = self._get_or_create_conversation(user_id, project_id)
        
        # Save user message
        user_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            user_id=user_id,
            role="user",
            content=user_message,
        )
        self.db.add(user_msg)
        self.db.commit()
        
        # Get conversation context
        context = self._get_conversation_context(conversation.id)
        
        # Create run for tracking
        run = self.create_run(
            input_context={"message": user_message, "attachments": attachments or []},
            user_id=user_id,
            project_id=project_id,
        )
        
        try:
            # Generate response using agent-specific logic
            self.update_run_status(run, RunStatus.RUNNING)
            response_data = self._generate_conversational_response(
                user_message=user_message,
                context=context,
                attachments=attachments,
                run_id=run.id,
            )
            
            # Save assistant message
            assistant_msg = ConversationMessage(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                user_id=None,  # AI message
                role="assistant",
                content=response_data.get("response", ""),
                run_id=run.id,
                model_used=self.agent.default_model,
            )
            self.db.add(assistant_msg)
            
            # Update conversation
            conversation.last_message_at = utc_now()
            conversation.updated_at = utc_now()
            
            # Create artifact if content was generated
            artifact = None
            if response_data.get("artifact_data"):
                artifact = self._create_artifact(
                    response_data["artifact_data"],
                    user_id,
                    project_id,
                    conversation.id,
                    run.id,
                )
            
            self.db.commit()
            self.update_run_status(run, RunStatus.SUCCESS)
            
            return {
                "success": True,
                "response": response_data.get("response", ""),
                "conversation_id": conversation.id,
                "message_id": assistant_msg.id,
                "run_id": run.id,
                "artifact_id": artifact.id if artifact else None,
                "metadata": response_data.get("metadata", {}),
            }
            
        except Exception as e:
            self.update_run_status(run, RunStatus.FAILED, str(e))
            self.db.commit()
            raise
    
    def _get_or_create_conversation(
        self,
        user_id: str,
        project_id: Optional[str] = None,
    ) -> Conversation:
        """Get existing conversation or create new one."""
        if self.conversation_id:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == self.conversation_id
            ).first()
            if conversation:
                return conversation
        
        # Create new conversation
        from app.middleware.request_context import get_context
        from app.config.constants import CTX_TENANT_ID
        
        tenant_id = get_context(CTX_TENANT_ID)
        
        conversation = Conversation(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            user_id=user_id,
            agent_id=self.agent.id,
            title=None,  # Will be auto-generated from first message
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        self.conversation_id = conversation.id
        return conversation
    
    def _get_conversation_context(self, conversation_id: str) -> str:
        """Get conversation history for context."""
        messages = self.db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).order_by(ConversationMessage.created_at.desc()).limit(10).all()
        
        context_parts = []
        for msg in reversed(messages):  # Reverse to get chronological order
            role = "User" if msg.role == "user" else "Assistant"
            context_parts.append(f"{role}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def _generate_conversational_response(
        self,
        user_message: str,
        context: str,
        attachments: Optional[List[Dict[str, Any]]],
        run_id: str,
    ) -> Dict[str, Any]:
        """
        Generate conversational response. Override in subclasses.
        
        Returns:
            Dict with 'response' (str) and optional 'artifact_data' (dict)
        """
        # Default implementation - use base agent's generate_response
        system_prompt = self.get_system_prompt()
        full_prompt = f"{system_prompt}\n\n{context}\n\nUser: {user_message}\n\nAssistant:"
        
        response = self.generate_response(
            user_prompt=user_message,
            context=context,
            run_id=run_id,
        )
        
        return {
            "response": response,
            "metadata": {},
        }
    
    def _create_artifact(
        self,
        artifact_data: Dict[str, Any],
        user_id: str,
        project_id: Optional[str],
        conversation_id: str,
        run_id: str,
    ) -> Artifact:
        """Create an artifact from generated content."""
        from app.middleware.request_context import get_context
        from app.config.constants import CTX_TENANT_ID
        
        tenant_id = get_context(CTX_TENANT_ID)
        
        artifact = Artifact(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            conversation_id=conversation_id,
            user_id=user_id,
            run_id=run_id,
            type=ArtifactType(artifact_data.get("type", "OTHER")),
            status=ArtifactStatus.DRAFT,
            title=artifact_data.get("title"),
            content=artifact_data.get("content"),
            content_data=artifact_data.get("content_data"),
            image_url=artifact_data.get("image_url"),
            video_url=artifact_data.get("video_url"),
            prompt_used=artifact_data.get("prompt_used"),
            model_used=self.agent.default_model,
        )
        
        self.db.add(artifact)
        return artifact
