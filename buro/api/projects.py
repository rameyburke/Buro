# buro/api/projects.py
#
# Projects API router for project management operations.
#
# Educational Notes for Junior Developers:
# - Project workspace management: Create, list, update containers.
# - Access control: Who can create/manage which projects.

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from buro.core.database import get_db
from buro.models import User, Project
from buro.api.auth import get_current_user

class ProjectCreateRequest(BaseModel):
    """Schema for creating new projects."""
    name: str
    key: str
    description: Optional[str] = None


class ProjectUpdateRequest(BaseModel):
    """Schema for updating projects."""
    name: Optional[str] = None
    key: Optional[str] = None
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    """Project information response schema."""
    id: str
    name: str
    key: str
    description: Optional[str]
    owner_id: str
    owner_name: Optional[str]
    default_assignee_id: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_project(cls, project: Project) -> "ProjectResponse":
        return cls(
            id=project.id,
            name=project.name,
            key=project.key,
            description=project.description,
            owner_id=project.owner_id,
            owner_name=getattr(project.owner, "full_name", None),
            default_assignee_id=project.default_assignee_id,
            created_at=project.created_at.isoformat(),
            updated_at=project.updated_at.isoformat()
        )

class ProjectListResponse(BaseModel):
    """Paginated project list response."""
    projects: List[ProjectResponse]

router = APIRouter()

@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List projects accessible to current user.

    Why filtered list: Multi-tenant security - users only see their projects.
    Different roles have different access patterns.
    """
    from buro.services.project_service import ProjectService

    project_service = ProjectService(db)

    try:
        projects = await project_service.list_user_projects(current_user)

        return ProjectListResponse(
            projects=[ProjectResponse.from_project(p) for p in projects]
        )
    except HTTPException:
        raise

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project workspace.

    Why controlled creation: Projects are containers with business rules.
    Only managers and admins can create new project workspaces.
    """
    from buro.services.project_service import ProjectService

    project_service = ProjectService(db)

    try:
        project = await project_service.create_project(
            name=request.name,
            key=request.key,
            description=request.description,
            owner=current_user
        )

        return ProjectResponse.from_project(project)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific project details.

    Why access control: Users can only see projects they have access to.
    Prevents information leakage between project workspaces.
    """
    from buro.services.project_service import ProjectService

    project_service = ProjectService(db)

    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Access control
    if not project_service._user_can_access_project(current_user, project):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )

    return ProjectResponse.from_project(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update project metadata with permission checks."""
    from buro.services.project_service import ProjectService

    project_service = ProjectService(db)

    updates = {k: v for k, v in request.model_dump(exclude_unset=True).items() if v is not None}

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )

    project = await project_service.update_project(project_id, updates, current_user)
    return ProjectResponse.from_project(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project workspace."""
    from buro.services.project_service import ProjectService

    project_service = ProjectService(db)
    await project_service.delete_project(project_id, current_user)
    return None

@router.get("/{project_id}/stats", response_model=dict)
async def get_project_stats(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project statistics for dashboards.

    Why separate endpoint: Statistics computation is expensive.
    Cached/pre-computed in production systems.
    """
    from buro.services.project_service import ProjectService

    project_service = ProjectService(db)

    try:
        stats = await project_service.get_project_stats(project_id, current_user)
        return stats
    except HTTPException:
        raise
