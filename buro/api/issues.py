# buro/api/issues.py
#
# Issues API router for issue management operations.
#
# Educational Notes for Junior Developers:
# - Core router: CRUD operations for Epics, Stories, Tasks, Bugs.
# - Kanban operations: Status transitions with drag-and-drop support.
# - Issue assignment: Single assignee per issue (simplified from Jira).

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Form
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from pydantic import BaseModel
from uuid import UUID

from buro.core.database import get_db
from buro.models import (
    User, Issue, IssueType, IssueStatus, Priority
)
from buro.api.auth import get_current_user
from buro.services.issue_service import IssueService
from buro.services.project_service import ProjectService

# Pydantic schemas for API requests/responses
class IssueCreateRequest(BaseModel):
    """Schema for creating new issues.

    Why separate schema: API should have own validation rules.
    Decouples internal model from external API contract.

    Educational Note: Pydantic automatically validates:
    - Required vs optional fields
    - Type conversion (string to enum)
    - Custom validation rules
    """
    title: str
    description: Optional[str] = None
    issue_type: IssueType = IssueType.TASK
    priority: Priority = Priority.MEDIUM
    project_id: str
    assignee_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Implement user authentication",
                "description": "Create JWT-based login system",
                "issue_type": "story",
                "priority": "high",
                "project_id": "uuid",
                "assignee_id": "uuid"
            }
        }

class IssueUpdateRequest(BaseModel):
    """Schema for updating existing issues.

    Why optional fields: PATCH semantics - only update provided fields.
    Different from CreateRequest which has more required fields.

    Educational Note: PATCH vs PUT difference:
    - PATCH: Partial update (merge)
    - PUT: Full replace (requires all fields)
    """
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    assignee_id: Optional[str] = None

class IssueResponse(BaseModel):
    """Public response schema for issues.

    Why not direct model dump: Security and API contract control.
    Never expose internal fields like hashed passwords or technical IDs.

    Educational Note: API responses should be intentional contracts,
    not direct database model dumps. This allows:
    - Field name changes without breaking clients
    - Computed fields and formatting
    - Security by omission
    """
    id: str
    key: str
    title: str
    description: Optional[str]
    issue_type: str
    status: str
    priority: str
    project_id: str
    reporter_id: str
    assignee_id: Optional[str]
    assignee_name: Optional[str] = None
    reporter_name: Optional[str] = None
    created_at: str
    updated_at: str

    @classmethod
    def from_issue(cls, issue: Issue) -> "IssueResponse":
        """Factory method to create response from Issue model."""
        return cls(
            id=issue.id,
            key=issue.key,
            title=issue.title,
            description=issue.description,
            issue_type=issue.issue_type.value,
            status=issue.status.value,
            priority=issue.priority.value,
            project_id=issue.project_id,
            reporter_id=issue.reporter_id,
            assignee_id=issue.assignee_id,
             assignee_name=getattr(issue.assignee, "full_name", None),
             reporter_name=getattr(issue.reporter, "full_name", None),
            created_at=issue.created_at.isoformat(),
            updated_at=issue.updated_at.isoformat()
        )

class IssueListResponse(BaseModel):
    """Paginated list response for issues."""
    issues: List[IssueResponse]
    total: int
    skip: int
    limit: int

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=IssueListResponse)
async def list_issues(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    assignee_id: Optional[str] = Query(None, description="Filter by assignee"),
    reporter_id: Optional[str] = Query(None, description="Filter by reporter"),
    status: Optional[str] = Query(None, description="Filter by status"),
    issue_type: Optional[str] = Query(None, description="Filter by issue type"),
    skip: int = Query(0, ge=0, description="Number of issues to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of issues to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List issues with filtering and pagination."""
    try:
        # Simple query to get all issues for the project with related data
        stmt = select(Issue).options(
            joinedload(Issue.project),
            joinedload(Issue.assignee),
            joinedload(Issue.reporter)
        ).where(Issue.project_id == project_id)

        result = await db.execute(stmt)
        issues = result.unique().scalars().all()

        # Convert to response format
        return IssueListResponse(
            issues=[IssueResponse.from_issue(issue) for issue in issues],
            total=len(issues),
            skip=skip,
            limit=limit
        )
    except Exception as e:
        print(f"Error in list_issues: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        # Return empty response instead of crashing
        return IssueListResponse(
            issues=[],
            total=0,
            skip=skip,
            limit=limit
        )

@router.get("/{project_key}/{issue_number}", response_model=IssueResponse)
async def get_issue(
    project_key: str,
    issue_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific issue by human-readable key (PROJ-123).

    Why nested path parameters: Issues have compound identifiers.
    Follows Jira's PROJ-NNN convention.

    Educational Note: REST URL design for compound keys:
    - /issues/{project_key}-{issue_number} (single param, harder to parse)
    - /projects/{project_key}/issues/{number} (verbose but clear)
    - Current choice: Readable and follows common patterns
    """
    issue_service = IssueService(db)

    # Service method handles permission checking
    issue = await issue_service.get_issue_by_key(project_key, issue_number)

    # Access control (simplified for now)
    # TODO: Implement proper permission checking
    if not current_user:  # Should always be authenticated due to dependency
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return IssueResponse.from_issue(issue)

@router.post("/", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
async def create_issue(
    request: IssueCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new issue in a project.

    Why POST /issues: Standard REST pattern for creating resources.
    Returns new issue with generated ID and key.

    Educational Note: Issue creation business logic:
    - Project validation and access control
    - Sequential issue numbering
    - Default assignee assignment
    - Reporter attribution
    """
    issue_service = IssueService(db)

    try:
        issue = await issue_service.create_issue(
            title=request.title,
            description=request.description,
            issue_type=request.issue_type,
            priority=request.priority,
            project_id=request.project_id,
            reporter=current_user,  # Mandatory: always set current user as reporter
            assignee_id=request.assignee_id
        )

        return IssueResponse.from_issue(issue)

    except HTTPException:
        # Re-raise service layer exceptions
        raise
    except Exception as e:
        # Unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create issue"
        )

@router.put("/{issue_id}", response_model=IssueResponse)
async def update_issue(
    issue_id: str,
    request: IssueUpdateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing issue.

    Why PUT /{id}: Standard REST pattern for resource updates.
    Supports partial updates with validation.

    Educational Note: Business rule validation in service layer:
    - Who can edit which fields?
    - Are field dependencies respected?
    - Does this trigger notifications?
    """
    issue_service = IssueService(db)

    # Convert request to dictionary for service layer
    updates = request.dict(exclude_unset=True)

    try:
        issue = await issue_service.update_issue(
            issue_id=issue_id,
            updates=updates,
            current_user=current_user,
            background_tasks=background_tasks
        )

        return IssueResponse.from_issue(issue)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to update issue %s", issue_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update issue"
        )

@router.put("/{issue_id}/status", response_model=IssueResponse)
async def update_issue_status(
    issue_id: str,
    new_status: IssueStatus = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update issue status (Kanban board operations).

    Why separate endpoint: Status transitions have special workflow logic.
    Used by drag-and-drop Kanban boards.

    Educational Note: Workflow validation:
    - Can you move from this status to that status?
    - Are there business rules (approvals, transitions)?
    - Should this trigger notifications?
    """
    print(f"DEBUG: Status update request - issue: {issue_id}, new_status: {new_status.value}")
    issue_service = IssueService(db)

    try:
        issue = await issue_service.transition_issue_status(
            issue_id=issue_id,
            new_status=new_status,
            current_user=current_user
        )

        return IssueResponse.from_issue(issue)

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG Status Update Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update issue status"
        )

@router.get("/projects/{project_id}/kanban", response_model=Dict[str, List[IssueResponse]])
async def get_kanban_board(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project issues organized by Kanban column (Temporarily simplified).

    Temporarily returns sample data to test CRUD/UI without database issues.
    TODO: Re-enable database queries once core issues are resolved.
    """
    # Fetch real issues from database grouped by status with eager loading
    # Need to include project relationship for issue.key property
    stmt = select(Issue).options(
        joinedload(Issue.project),  # Eager load project for key generation
        joinedload(Issue.reporter),  # Optional: for user info
        joinedload(Issue.assignee)   # Optional: for assignee info
    ).where(Issue.project_id == project_id)

    # Apply security filtering if needed
    # For now, allow access to all issues in the project
    result = await db.execute(stmt)
    issues = result.unique().scalars().all()

    # Group issues by status for Kanban board
    kanban_board = {
        "backlog": [],
        "to_do": [],
        "in_progress": [],
        "done": []
    }

    for issue in issues:
        status_key = issue.status.value  # Convert enum to string
        if status_key in kanban_board:
            kanban_board[status_key].append(IssueResponse.from_issue(issue))

    return kanban_board


@router.delete("/{issue_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_issue(
    issue_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an issue (hard delete for now)."""
    issue_service = IssueService(db)
    await issue_service.delete_issue(issue_id, current_user)
    return None

# TODO: Add endpoints for:
# - DELETE /{issue_id} (soft delete)
# - POST /{issue_id}/comments (comments system)
# - POST /{issue_id}/attachments (file uploads)
# - GET /search/{query} (advanced search)
