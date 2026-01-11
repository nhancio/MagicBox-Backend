"""
Reel Agent - Specialized agent for generating Instagram Reels/TikTok scripts.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models.agent import Agent
from app.db.models.run import Run, RunStatus
from app.ai.agents.base_agent import BaseAgent
from app.services.ai_service import AIService
from app.services.ai_video_service import AIVideoService
from app.ai.observability.langfuse_client import LangfuseClient
from app.utils.time import utc_now


class ReelAgent(BaseAgent):
    """Agent specialized for reel/video generation (script + video)."""
    
    def execute(self, input_data: Dict[str, Any], run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a reel script and optionally generate video using Veo 3.1.
        
        Expected input_data:
        - topic: str
        - duration_seconds: int (optional, default 30)
        - style: str (optional)
        - hook: str (optional)
        - generate_video: bool (optional, default False) - If True, also generates video
        - video_output_path: str (optional) - Path to save generated video
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
            
            # Get system prompt and track with Langfuse
            system_prompt = self.get_system_prompt()
            langfuse_trace_id = None
            try:
                langfuse_trace_id = LangfuseClient.trace_run(
                    run_id=run_id or "",
                    agent_name=self.agent.name,
                    input_data={"topic": topic, "system_prompt": system_prompt, "context": context},
                )
            except Exception:
                pass
            
            # Generate reel script using Gemini 3 Pro
            result = AIService.generate_reel_script(
                topic=topic,
                duration_seconds=input_data.get("duration_seconds", 30),
                style=input_data.get("style", "engaging"),
                hook=input_data.get("hook"),
            )
            
            if not result.get("success"):
                raise Exception(result.get("error", "Failed to generate reel script"))
            
            # Optionally generate video using Veo 3.1
            video_result = None
            if input_data.get("generate_video", False):
                # Build video prompt from script
                video_prompt = f"{result.get('hook', '')} {result.get('script', '')}"
                if input_data.get("style"):
                    video_prompt = f"{video_prompt}, style: {input_data.get('style')}"
                
                video_result = AIVideoService.generate_video(
                    prompt=video_prompt,
                    output_path=input_data.get("video_output_path"),
                )
            
            # Update Langfuse trace
            if langfuse_trace_id:
                try:
                    LangfuseClient.trace_generation(
                        trace_id=langfuse_trace_id,
                        name="reel_generation",
                        model="gemini-3-pro-preview",
                        input_data={"topic": topic},
                        output_data={**result, "video": video_result} if video_result else result,
                    )
                except Exception:
                    pass
            
            # Update run if exists
            if run:
                run.output_data = {**result, "video": video_result} if video_result else result
                run.status = RunStatus.SUCCESS
                run.completed_at = utc_now()
                self.db.commit()
            
            response = {
                "success": True,
                "script": result.get("script"),
                "hook": result.get("hook"),
                "scenes": result.get("scenes", []),
                "call_to_action": result.get("call_to_action"),
                "metadata": result.get("metadata", {}),
            }
            
            if video_result and video_result.get("success"):
                response["video"] = {
                    "video_path": video_result.get("video_path"),
                    "metadata": video_result.get("metadata", {}),
                }
            
            return response
            
        except Exception as e:
            if run:
                self.update_run_status(run, RunStatus.FAILED, str(e))
            raise
