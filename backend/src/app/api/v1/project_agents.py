"""
Project-Agent API endpoints - Manage agent assignments to projects.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.project import Project
from app.db.models.agent import Agent
from app.db.models.project_agent import ProjectAgent
from app.dependencies.auth import get_current_user, require_project

router = APIRouter(prefix="/projects/{project_id}/agents", tags=["Project Agents"])


class AttachAgentRequest(BaseModel):
    agent_id: str
    config_override: Optional[dict] = None


@router.post("/attach", status_code=status.HTTP_201_CREATED)
def attach_agent_to_project(
    project_id: str,
    request: AttachAgentRequest,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Attach an agent to a project."""
    # Verify project_id matches
    if project_id != current_project.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID mismatch"
        )
    
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == request.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Check if already attached
    existing = db.query(ProjectAgent).filter(
        ProjectAgent.project_id == project_id,
        ProjectAgent.agent_id == request.agent_id
    ).first()
    
    if existing:
        # Update existing
        if request.config_override:
            existing.config_override = request.config_override
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return {
            "success": True,
            "message": "Agent already attached, updated configuration",
            "project_agent": {
                "id": existing.id,
                "project_id": existing.project_id,
                "agent_id": existing.agent_id,
            }
        }
    
    # Create new attachment
    project_agent = ProjectAgent(
        project_id=project_id,
        agent_id=request.agent_id,
        config_override=request.config_override,
    )
    
    db.add(project_agent)
    db.commit()
    db.refresh(project_agent)
    
    return {
        "success": True,
        "message": "Agent attached to project",
        "project_agent": {
            "id": project_agent.id,
            "project_id": project_agent.project_id,
            "agent_id": project_agent.agent_id,
        }
    }


@router.get("/", status_code=status.HTTP_200_OK)
def list_project_agents(
    project_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """
    List all available agents for a project.
    Shows all available agents (global + tenant-specific) with attachment status.
    """
    # Verify project_id matches
    if project_id != current_project.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID mismatch"
        )
    
    tenant_id = current_user.tenant_id
    
    # Get all available agents (global and tenant-specific)
    all_agents = db.query(Agent).filter(
        (Agent.tenant_id == None) | (Agent.tenant_id == tenant_id),
        Agent.is_active == True
    ).all()
    
    # Get attached agents for this project
    attached_agent_ids = set()
    project_agents_map = {}
    project_agents = db.query(ProjectAgent).filter(
        ProjectAgent.project_id == project_id,
        ProjectAgent.is_active == True
    ).all()
    
    for pa in project_agents:
        attached_agent_ids.add(pa.agent_id)
        project_agents_map[pa.agent_id] = pa
    
    # Build response with all agents and their attachment status
    agents = []
    for agent in all_agents:
        is_attached = agent.id in attached_agent_ids
        project_agent = project_agents_map.get(agent.id)
        
        agent_data = {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "role": agent.role,
            "default_model": agent.default_model,
            "version": agent.version,
            "is_attached": is_attached,
        }
        
        if is_attached and project_agent:
            agent_data["project_agent_id"] = project_agent.id
            agent_data["config_override"] = project_agent.config_override
            agent_data["attached_at"] = project_agent.created_at.isoformat()
        
        agents.append(agent_data)
    
    return {
        "success": True,
        "project_id": project_id,
        "agents": agents,
        "total_available": len(agents),
        "total_attached": len(attached_agent_ids),
    }


@router.delete("/{agent_id}", status_code=status.HTTP_200_OK)
def detach_agent_from_project(
    project_id: str,
    agent_id: str,
    current_user: User = Depends(get_current_user),
    current_project: Project = Depends(require_project),
    db: Session = Depends(get_db),
):
    """Detach an agent from a project."""
    # Verify project_id matches
    if project_id != current_project.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID mismatch"
        )
    
    project_agent = db.query(ProjectAgent).filter(
        ProjectAgent.project_id == project_id,
        ProjectAgent.agent_id == agent_id
    ).first()
    
    if not project_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not attached to this project"
        )
    
    project_agent.is_active = False
    db.commit()
    
    return {
        "success": True,
        "message": "Agent detached from project",
    }
