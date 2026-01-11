"""
AI Runs API endpoints - Execute and manage AI agent runs.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.db.models.run import Run, RunStatus
from app.ai.orchestrator.run_executor import RunExecutor
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/projects/{project_id}/ai-runs", tags=["AI Runs"])


class RunExecuteRequest(BaseModel):
    agent_name: str
    input_data: Dict[str, Any]
    project_id: Optional[str] = None


@router.post("/execute")
def execute_run(
    project_id: str,
    request: RunExecuteRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Execute an AI agent run."""
    try:
        from app.db.models.agent import Agent
        from app.ai.agents.base_agent import BaseAgent
        
        # Get agent
        agent = db.query(Agent).filter(Agent.name == request.agent_name).first()
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{request.agent_name}' not found"
            )
        
        # Create run
        run = BaseAgent(
            db=db,
            agent=agent,
            conversation_id=None,
        ).create_run(
            input_context=request.input_data,
            user_id=current_user.id,
            project_id=request.project_id or current_project.id,
        )
        
        # Execute run
        executor = RunExecutor(db)
        result = executor.execute_run(run, request.input_data)
        
        return {
            "success": True,
            "run_id": run.id,
            "result": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{run_id}")
def get_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get run details."""
    run = db.query(Run).filter(
        Run.id == run_id,
        Run.tenant_id == current_user.tenant_id
    ).first()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )
    
    return {
        "success": True,
        "run": {
            "id": run.id,
            "status": run.status.value,
            "agent_name": run.agent_name,
            "output_data": run.output_data,
            "error_message": run.error_message,
        }
    }
