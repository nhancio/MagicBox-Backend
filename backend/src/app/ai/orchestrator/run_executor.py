"""
Run Executor - Executes AI agent runs with proper error handling and tracking.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.db.models.run import Run, RunStatus
from app.db.models.agent import Agent
from app.ai.agents.base_agent import BaseAgent
from app.ai.agents.post_agent import PostAgent
from app.ai.agents.reel_agent import ReelAgent
from app.ai.agents.image_agent import ImageAgent
from app.ai.orchestrator.retry_policy import RetryPolicy, RetryStrategy
from app.utils.time import utc_now


class RunExecutor:
    """Executes AI agent runs."""
    
    AGENT_CLASS_MAP = {
        "post_agent": PostAgent,
        "reel_agent": ReelAgent,
        "image_agent": ImageAgent,
    }
    
    def __init__(self, db: Session, retry_policy: Optional[RetryPolicy] = None):
        self.db = db
        self.retry_policy = retry_policy or RetryPolicy(
            max_retries=2,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        )
    
    def execute_run(self, run: Run, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a run."""
        # Get agent
        agent = self.db.query(Agent).filter(Agent.id == run.agent_id).first()
        if not agent:
            raise ValueError(f"Agent {run.agent_id} not found")
        
        # Get agent class
        agent_class = self.AGENT_CLASS_MAP.get(agent.name, BaseAgent)
        
        # Create agent instance
        agent_instance = agent_class(
            db=self.db,
            agent=agent,
            conversation_id=run.conversation_id,
        )
        
        # Update run status
        run.status = RunStatus.RUNNING
        run.started_at = utc_now()
        self.db.commit()
        
        try:
            # Execute with retry policy
            result = self.retry_policy.execute(
                agent_instance.execute,
                input_data=input_data,
                run_id=run.id,
            )
            
            # Update run with success
            run.status = RunStatus.SUCCESS
            run.completed_at = utc_now()
            run.output_data = result
            self.db.commit()
            
            return result
            
        except Exception as e:
            # Update run with failure
            run.status = RunStatus.FAILED
            run.completed_at = utc_now()
            run.error_message = str(e)
            self.db.commit()
            raise
