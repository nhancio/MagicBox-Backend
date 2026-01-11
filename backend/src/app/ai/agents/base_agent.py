"""
Base Agent - Abstract base class for all AI agents.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.db.models.agent import Agent
from app.db.models.run import Run, RunStatus
from app.services.ai_service import AIService
from app.services.prompt_loader import PromptLoader
from app.ai.memory.session_memory import SessionMemory
from app.ai.memory.long_term_memory import LongTermMemory
from app.ai.memory.episodic_memory import EpisodicMemory
from app.ai.observability.langfuse_client import LangfuseClient
from app.utils.time import utc_now
import uuid


class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(self, db: Session, agent: Agent, conversation_id: Optional[str] = None):
        self.db = db
        self.agent = agent
        self.conversation_id = conversation_id
        
        # Initialize memory systems
        if conversation_id:
            self.session_memory = SessionMemory(db, conversation_id)
        else:
            self.session_memory = None
        
        self.long_term_memory = LongTermMemory(db)
        self.episodic_memory = EpisodicMemory(db)
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any], run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the agent's main logic.
        
        Args:
            input_data: Input data for the agent
            run_id: Optional run ID for tracking
            
        Returns:
            Execution result
        """
        pass
    
    def create_run(
        self,
        input_context: Dict[str, Any],
        user_id: str,
        project_id: Optional[str] = None,
    ) -> Run:
        """Create a new run for tracking."""
        from app.middleware.request_context import get_context
        from app.config.constants import CTX_TENANT_ID
        
        tenant_id = get_context(CTX_TENANT_ID)
        
        run = Run(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            conversation_id=self.conversation_id,
            user_id=user_id,
            agent_id=self.agent.id,
            agent_name=self.agent.name,
            status=RunStatus.PENDING,
            input_context=input_context,
            model_name=self.agent.default_model,
        )
        
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
    
    def update_run_status(self, run: Run, status: RunStatus, error_message: Optional[str] = None):
        """Update run status."""
        run.status = status
        if error_message:
            run.error_message = error_message
        if status == RunStatus.RUNNING:
            run.started_at = utc_now()
        elif status in [RunStatus.SUCCESS, RunStatus.FAILED]:
            run.completed_at = utc_now()
        self.db.commit()
    
    def get_context(self, query: Optional[str] = None) -> str:
        """Get relevant context from memory systems."""
        context_parts = []
        
        # Session memory
        if self.session_memory:
            recent_history = self.session_memory.get_recent_history(last_n=5)
            if recent_history:
                context_parts.append("Recent conversation:")
                for msg in recent_history:
                    context_parts.append(f"{msg['role']}: {msg['content'][:100]}")
        
        # Long-term memory (if query provided)
        if query:
            relevant_context = self.long_term_memory.get_relevant_context(query, limit=3)
            if relevant_context:
                context_parts.append("\nRelevant context:")
                context_parts.append(relevant_context)
        
        return "\n".join(context_parts)
    
    def get_system_prompt(self) -> str:
        """Get system prompt for this agent from JSON file."""
        # Try to load from JSON file first
        try:
            prompt_data = PromptLoader.load_prompt(self.agent.name)
            return prompt_data.get("system_prompt", "")
        except Exception:
            # Fallback to agent's stored system_prompt
            return self.agent.system_prompt or ""
    
    def generate_response(
        self,
        user_prompt: str,
        context: Optional[str] = None,
        model: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> str:
        """Generate AI response using AIService with Langfuse tracking."""
        # Get system prompt from JSON file
        system_prompt = self.get_system_prompt()
        
        # Build full prompt with context
        full_prompt = user_prompt
        if context:
            full_prompt = f"{context}\n\n{user_prompt}"
        
        # Get prompt config (model, temperature, etc.)
        prompt_config = PromptLoader.get_prompt_config(self.agent.name)
        model_name = model or prompt_config.get("model") or self.agent.default_model or "gemini-pro"
        
        # Track with Langfuse if available
        langfuse_trace_id = None
        try:
            LangfuseClient.trace_run(
                run_id=run_id or "",
                agent_name=self.agent.name,
                input_data={"prompt": full_prompt, "system_prompt": system_prompt},
            )
        except Exception:
            pass  # Langfuse is optional
        
        # Generate using AIService
        try:
            # Use the appropriate model based on agent configuration
            # For now, using AIService methods - in production would use direct LLM calls
            if "post" in self.agent.name.lower():
                result = AIService.generate_post(
                    topic=full_prompt,
                    tone="professional",
                )
                return result.get("content", "")
            elif "reel" in self.agent.name.lower():
                result = AIService.generate_reel_script(
                    topic=full_prompt,
                    duration_seconds=30,
                )
                return result.get("script", "")
            else:
                # Generic fallback
                result = AIService.generate_post(
                    topic=full_prompt,
                    tone="professional",
                )
                return result.get("content", "")
        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}")
