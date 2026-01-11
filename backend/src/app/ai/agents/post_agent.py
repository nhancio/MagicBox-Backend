"""
Post Agent - Specialized agent for generating social media posts.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models.agent import Agent
from app.db.models.run import Run, RunStatus
from app.ai.agents.base_agent import BaseAgent
from app.services.ai_service import AIService
from app.ai.observability.langfuse_client import LangfuseClient


class PostAgent(BaseAgent):
    """Agent specialized for social media post generation."""
    
    def execute(self, input_data: Dict[str, Any], run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a social media post.
        
        Expected input_data:
        - topic: str
        - tone: str (optional)
        - platform: str (optional)
        - target_audience: str (optional)
        - hashtags: bool (optional)
        """
        run = None
        if run_id:
            run = self.db.query(Run).filter(Run.id == run_id).first()
            if run:
                self.update_run_status(run, RunStatus.RUNNING)
        
        try:
            topic = input_data.get("topic", "")
            if not topic:
                raise ValueError("Topic is required")
            
            # Get context from memory
            context = self.get_context(query=topic)
            
            # Get system prompt and build full prompt
            system_prompt = self.get_system_prompt()
            user_prompt = f"Generate a {input_data.get('tone', 'professional')} social media post about: {topic}"
            if input_data.get("platform"):
                user_prompt += f" for {input_data.get('platform')}"
            if input_data.get("target_audience"):
                user_prompt += f" targeting {input_data.get('target_audience')}"
            
            # Generate post using AIService with Langfuse tracking
            langfuse_trace_id = None
            try:
                langfuse_trace_id = LangfuseClient.trace_run(
                    run_id=run_id or "",
                    agent_name=self.agent.name,
                    input_data={"prompt": user_prompt, "system_prompt": system_prompt, "context": context},
                )
            except Exception:
                pass
            
            result = AIService.generate_post(
                topic=topic,
                tone=input_data.get("tone", "professional"),
                platform=input_data.get("platform"),
                target_audience=input_data.get("target_audience"),
                hashtags=input_data.get("hashtags", True),
            )
            
            # Update Langfuse trace with output
            if langfuse_trace_id and result.get("success"):
                try:
                    LangfuseClient.trace_generation(
                        trace_id=langfuse_trace_id,
                        name="post_generation",
                        model="gemini-pro",
                        input_data={"topic": topic},
                        output_data=result,
                    )
                except Exception:
                    pass
            
            if not result.get("success"):
                raise Exception(result.get("error", "Failed to generate post"))
            
            # Update run if exists
            if run:
                from app.utils.time import utc_now
                run.output_data = result
                run.status = RunStatus.SUCCESS
                run.completed_at = utc_now()
                self.db.commit()
            
            return {
                "success": True,
                "content": result.get("content"),
                "hashtags": result.get("hashtags", []),
                "metadata": result.get("metadata", {}),
            }
            
        except Exception as e:
            if run:
                self.update_run_status(run, RunStatus.FAILED, str(e))
            raise
