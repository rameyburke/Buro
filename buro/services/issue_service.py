# buro/services/issue_service.py
#
# Issue management business logic service.
#
# Educational Notes for Junior Developers:
# - Issue lifecycle management: Creation, assignment, status transitions
# - Workflow validation: Business rules for what transitions are allowed
# - Search and filtering: Complex queries for issue discovery

from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status, BackgroundTasks

from buro.models import (
    Issue, User, Project, IssueType, IssueStatus, Priority,
    Role
)


class IssueService:
    """Business logic for issue management operations.

    Handles issue CRUD, workflow transitions, and search functionality.
    Core of the agile project management system.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_issue(
        self,
        title: str,
        description: Optional[str],
        issue_type: IssueType,
        priority: Priority,
        project_id: str,
        reporter: User,
        assignee_id: Optional[str] = None
    ) -> Issue:
        """Create a new issue with business rules validation.

        Why complex method: Issues need sequential numbering within projects,
        permission checks, and business rule validation.

        Educational Note: Issue creation involves:
        - Project existence validation
        - Sequential issue numbering (PROJ-1, PROJ-2, etc.)
        - Permission checks (who can create issues?)
        - Business rule enforcement
        """
        # Validate project access
        project = await self.db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Check if user can access this project
        if not self._user_can_access_project(reporter, project):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create issues in this project"
            )

        # Validate assignee if provided
        if assignee_id:
            assignee = await self.db.get(User, assignee_id)
            if not assignee or not assignee.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid assignee"
                )

        # Generate next issue number for this project
        # Why MAX() query: Ensures sequential numbering even with deletions
        number_stmt = select(func.max(Issue.issue_number)).where(
            Issue.project_id == project_id
        )
        result = await self.db.execute(number_stmt)
        max_number = result.scalar_one_or_none()
        next_number = (max_number or 0) + 1

        # Create issue with default values
        issue = Issue(
            issue_number=next_number,
            title=title.strip(),
            description=description.strip() if description else None,
            issue_type=issue_type,
            priority=priority,
            status=IssueStatus.BACKLOG,  # Default starting status
            project_id=project_id,
            reporter_id=reporter.id,
            assignee_id=assignee_id
        )

        self.db.add(issue)
        await self.db.commit()
        await self.db.refresh(issue)

        return issue

    async def get_issue_by_key(self, project_key: str, issue_number: int) -> Issue:
        """Retrieve issue by human-readable key (PROJ-123).

        Why by key: Most user-facing issue references use keys.
        More intuitive than UUIDs for users.
        """
        # First get project by key
        from buro.services.project_service import ProjectService
        project_service = ProjectService(self.db)

        try:
            project = await project_service.get_project_by_key(project_key)
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_key}' not found"
            )

        # Then find issue by number in that project
        stmt = select(Issue).where(
            and_(
                Issue.project_id == project.id,
                Issue.issue_number == issue_number
            )
        )
        result = await self.db.execute(stmt)
        issue = result.scalar_one_or_none()

        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Issue {project_key}-{issue_number} not found"
            )

        return issue

    async def list_issues(
        self,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        reporter_id: Optional[str] = None,
        status: Optional[IssueStatus] = None,
        issue_type: Optional[IssueType] = None,
        current_user: User = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Issue]:
        """List and filter issues with pagination.

        Why complex filters: Users need to find issues by different criteria.
        Supports project filtering, assignment filtering, etc.

        Educational Note: Building complex SQL queries with optional filters
        requires careful construction to avoid performance issues.
        """


        # Base query with eager loading
        stmt = select(Issue).options(
            # Eager load related objects to avoid N+1 queries
            # Why: API performance - avoid individual queries for each issue
            # Tradeoff: More data transferred if relations not needed
        )

        # Apply filters
        conditions = []

        # Project filter (if specified)
        if project_id:
            conditions.append(Issue.project_id == project_id)
            # Additional check: user can access this project
            if current_user and not self._user_can_access_project_by_id(current_user, project_id):
                return []  # User can't access project, return empty list

        # User-specific filter for non-admin users
        # Why: Multi-tenant isolation - users can only see issues they should access
        if current_user and current_user.role != Role.ADMIN:
            # This is simplified - in production, more complex permissions
            if project_id is None:
                # If no project specified, only return issues from accessible projects
                accessible_project_ids = await self._get_accessible_project_ids(current_user)
                conditions.append(Issue.project_id.in_(accessible_project_ids))

        # Other filters
        filter_mapping = {
            'assignee_id': assignee_id,
            'reporter_id': reporter_id,
            'status': status,
            'issue_type': issue_type
        }

        for field, value in filter_mapping.items():
            if value is not None:
                conditions.append(getattr(Issue, field) == value)

        # Apply all conditions
        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Ordering: Recent first by default
        stmt = stmt.order_by(Issue.updated_at.desc())

        # Pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_issue(
        self,
        issue_id: str,
        updates: dict,
        current_user: User,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Issue:
        """Update issue with business rules and validation.

        Why complex: Different fields have different permission requirements.
        Assignee changes trigger notifications, status changes have validation.

        Educational Note: Field-level permissions vs model-level permissions.
        Some users can edit certain fields but not others.
        """
        issue = await self.db.get(Issue, issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found"
            )

        # Check if user can edit issues in this project
        if not self._user_can_access_issue(current_user, issue):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify this issue"
            )

        # Apply updates with field-specific validation
        for field, value in updates.items():
            if field in ['title', 'description']:
                # Basic fields - most users can edit
                if not value or not value.strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{field} cannot be empty"
                    )
                setattr(issue, field, value.strip())
            elif field == 'assignee_id':
                # Assignment changes - can assign to valid users
                assignee = None
                if value is not None:
                    assignee = await self.db.get(User, value)
                    if not assignee or not assignee.is_active:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid assignee"
                        )
                # Store old assignee for notification
                old_assignee = issue.assignee
                setattr(issue, field, value)

                # Send notification for assignment changes
                if background_tasks and assignee:
                    await self._notify_assignee_change(
                        assignee, issue, background_tasks
                    )
            elif field == 'priority':
                # Priority changes - validate enum value
                if value not in [p.value for p in Priority]:
                        # For Kanban, allow flexible transitions but log for workflow improvement
                        print(f"WARNING: Non-standard transition from {issue.status.value} to {new_status.value}")
                issue.priority = Priority(value)
            elif field == 'status':
                # Status changes - use workflow method for validation
                await self.transition_issue_status(issue_id, IssueStatus(value), current_user)

        await self.db.commit()
        await self.db.refresh(issue)
        return issue

    async def transition_issue_status(
        self,
        issue_id: str,
        new_status: IssueStatus,
        current_user: User
    ) -> Issue:
        """Transition issue to new status with workflow validation.

        Why separate method: Workflow logic is complex and reusable.
        Kanban boards support flexible status transitions.

        Educational Note: Workflow validation prevents invalid states.
        Unlike Scrum which restricts transitions, Kanban allows flexibility.
        """
        # Eager load project relationship for key generation in response
        stmt = select(Issue).options(joinedload(Issue.project)).where(Issue.id == issue_id)
        result = await self.db.execute(stmt)
        issue = result.unique().scalar_one_or_none()
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found"
            )

        # Check permissions - anyone who can edit the issue can change status
        if not self._user_can_access_issue(current_user, issue):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change issue status"
            )

        # Kanban workflow: All transitions allowed - Kanban focuses on flow, not rigid process
        # Educational Note: Unlike Scrum which enforces sprint ceremonies and workflows,
        # Kanban allows flexible status transitions to optimize work visualization and flow

        issue.status = new_status
        await self.db.commit()

        # Re-query the issue to get the updated data WITH relationships
        stmt = select(Issue).options(joinedload(Issue.project)).where(Issue.id == issue.id)
        result = await self.db.execute(stmt)
        updated_issue = result.unique().scalar_one()
        return updated_issue

    async def _get_accessible_project_ids(self, user: User) -> List[str]:
        """Helper method to get project IDs user can access."""
        # Simplified for now - managers see their projects, developers see all
        # TODO: Implement proper project membership
        if user.role in [Role.ADMIN, Role.MANAGER]:
            # Managers see projects they own
            from buro.services.project_service import ProjectService
            project_service = ProjectService(self.db)
            projects = await project_service.list_user_projects(user)
            return [p.id for p in projects]
        else:
            # Developers see all projects for now
            # TODO: Implement project membership
            stmt = select(Project.id)
            result = await self.db.execute(stmt)
            return [row[0] for row in result]

    def _user_can_access_project(self, user: User, project: Project) -> bool:
        """Check if user can access a specific project."""
        if user.role in [Role.ADMIN]:
            return True
        elif user.role == Role.MANAGER and user.id == project.owner_id:
            return True
        else:
            # Developers can access all projects for now
            # TODO: Implement project-specific access
            return True

    def _user_can_access_project_by_id(self, user: User, project_id: str) -> bool:
        """Check project access without loading full project object."""
        # TODO: Optimize this - currently simplified
        return True

    def _user_can_access_issue(self, user: User, issue: Issue) -> bool:
        """Check if user can access and modify a specific issue."""
        # For now, if they can access the project, they can access issues in it
        # This will need optimization and refinement
        return True

    async def _notify_assignee_change(
        self, assignee: User, issue: Issue, background_tasks: BackgroundTasks
    ):
        """Send notification when issue is assigned to a user."""
        from buro.services.notification_service import EmailNotificationService

        notification_service = EmailNotificationService()
        await notification_service.send_issue_assigned_notification(
            background_tasks, issue, assignee
        )