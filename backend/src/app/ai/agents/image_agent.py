"""
Image Agent - Specialized agent for image generation and optimization.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models.agent import Agent
from app.db.models.run import Run, RunStatus
from app.ai.agents.base_agent import BaseAgent
from app.services.ai_image_service import AIImageService
from app.ai.observability.langfuse_client import LangfuseClient
from app.utils.time import utc_now


class ImageAgent(BaseAgent):
    """Agent specialized for image generation using Gemini 2.5 Flash Image."""
    
    def execute(self, input_data: Dict[str, Any], run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate images using Gemini 2.5 Flash Image model.
        
        Expected input_data:
        - prompt: str (image generation prompt)
        - style: str (optional)
        - output_path: str (optional, path to save image)
        """
        run = None
        if run_id:
            run = self.db.query(Run).filter(Run.id == run_id).first()
            if run:
                self.update_run_status(run, RunStatus.RUNNING)
        
        try:
            prompt = input_data.get("prompt", "")
            if not prompt:
                raise ValueError("Prompt is required")
            
            # Enhance prompt with style if provided
            full_prompt = prompt
            if input_data.get("style"):
                full_prompt = f"{prompt}, style: {input_data.get('style')}"
            
            # Get system prompt and track with Langfuse
            system_prompt = self.get_system_prompt()
            langfuse_trace_id = None
            try:
                langfuse_trace_id = LangfuseClient.trace_run(
                    run_id=run_id or "",
                    agent_name=self.agent.name,
                    input_data={"prompt": full_prompt, "system_prompt": system_prompt},
                )
            except Exception:
                pass
            
            # Generate image using Gemini 2.5 Flash Image
            result = AIImageService.generate_image(
                prompt=full_prompt,
                output_path=input_data.get("output_path"),
            )
            
            if not result.get("success"):
                raise Exception(result.get("error", "Failed to generate image"))
            
            # Update Langfuse trace
            if langfuse_trace_id:
                try:
                    LangfuseClient.trace_generation(
                        trace_id=langfuse_trace_id,
                        name="image_generation",
                        model="gemini-2.5-flash-image",
                        input_data={"prompt": full_prompt},
                        output_data=result,
                    )
                except Exception:
                    pass
            
            # Update run if exists
            if run:
                run.output_data = result
                run.status = RunStatus.SUCCESS
                run.completed_at = utc_now()
                self.db.commit()
            
            return {
                "success": True,
                "image_path": result.get("image_path"),
                "prompt": full_prompt,
                "metadata": result.get("metadata", {}),
            }
            
        except Exception as e:
            if run:
                self.update_run_status(run, RunStatus.FAILED, str(e))
            raise
