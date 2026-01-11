"""
Agents API endpoints - manage AI agents.
Requires authentication and an active project.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.db.models.agent import Agent
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("/", response_model=List[dict])
def list_agents(
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    List all available agents (global and tenant-specific).
    Requires authentication and a project.
    """
    tenant_id = current_user.tenant_id
    
    # Get global agents (tenant_id is None) and tenant-specific agents
    agents = db.query(Agent).filter(
        (Agent.tenant_id == None) | (Agent.tenant_id == tenant_id),
        Agent.is_active == True
    ).all()
    
    return [
        {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "role": agent.role,
            "default_model": agent.default_model,
            "version": agent.version,
        }
        for agent in agents
    ]


@router.get("/{agent_id}", response_model=dict)
def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    Get an agent by ID.
    Requires authentication and a project.
    """
    tenant_id = current_user.tenant_id
    
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        (Agent.tenant_id == None) | (Agent.tenant_id == tenant_id),
        Agent.is_active == True
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "role": agent.role,
        "default_model": agent.default_model,
        "tools": agent.tools,
        "system_prompt": agent.system_prompt,
        "version": agent.version,
    }
