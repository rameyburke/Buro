# buro/services/project_service.py
#
# Project management business logic service.
#
# Educational Notes for Junior Developers:
# - Project lifecycle management: Creation, membership, permissions
# - Business rules for projects: Unique keys, ownership transfers
# - Access control: Who can create, modify, or delete projects

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from buro.models import Project, User, Role, Issue, IssueStatus


class ProjectService:
    """Business logic for project management operations.

    Handles project lifecycle, membership, and access control.
    Projects are workspace containers that own issues.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(
        self,
        name: str,
        key: str,
        description: Optional[str],
        owner: User
    ) -> Project:
        """Create a new project with business rules validation.

        Why business rules here: Project keys must be unique, uppercase,
        alphanumeric. Only certain roles can create projects.

        Educational Note: Project keys are human-readable identifiers
        that appear in issue IDs (PROJ-123). Must be unique and memorable.
        """
        # Permission check - managers and admins can create projects
        if owner.role not in [Role.ADMIN, Role.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create projects"
            )

        # Validate project key (business rules)
        key = key.upper().strip()
        if not key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project key cannot be empty"
            )

        if not all(c.isalnum() and c.isascii() for c in key):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project key must be alphanumeric ASCII characters only"
            )

        if len(key) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project key cannot exceed 10 characters"
            )

        # Check uniqueness (case-insensitive)
        existing_stmt = select(Project).where(func.lower(Project.key) == key.lower())
        result = await self.db.execute(existing_stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project key '{key}' already exists"
            )

        # Create project
        project = Project(
            name=name.strip(),
            key=key,
            description=description.strip() if description else None,
            owner_id=owner.id
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def get_project_by_key(self, project_key: str) -> Project:
        """Retrieve project by human-readable key.

        Why not by ID: Keys are used in UI and issue references.
        Easier for users to remember and type.

        Educational Note: Projects are referenced by keys everywhere:
        - UI urls: /projects/MYPROJ
        - Issue IDs: MYPROJ-123
        """
        key_upper = project_key.upper().strip()
        stmt = select(Project).where(func.lower(Project.key) == key_upper.lower())
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_key}' not found"
            )

        return project

    async def list_user_projects(self, user: User) -> List[Project]:
        """List projects accessible to a user.

        Why complex logic: Users can access:
        - Projects they own (managers)
        - Projects they're assigned to (developers)
        - All projects (admins)

        Educational Note: This implements the multi-tenant access control
        that makes projects act as isolated workspaces.
        """
        loader = selectinload(Project.owner)
        if user.role == Role.ADMIN:
            stmt = select(Project).options(loader)
        else:
            stmt = select(Project).where(Project.owner_id == user.id).options(loader)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_project(
        self,
        project_id: str,
        updates: dict,
        current_user: User
    ) -> Project:
        """Update project details with access control.

        Why permission checks: Only project owners can modify their projects.
        Admins can modify any project.

        Educational Note: Business rules for updates:
        - Key changes require uniqueness validation
        - Ownership can be transferred (with care)
        """
        project = await self.db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        if not self._user_can_access_project(current_user, project):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only edit projects you own"
            )

        # Apply updates with validation
        for field, value in updates.items():
            if field == "key":
                # Key change requires re-validation
                new_key = value.upper().strip()
                if new_key != project.key:
                    await self._validate_project_key_unique(new_key, exclude_id=project_id)
                project.key = new_key
            elif field in ["name", "description"]:
                setattr(project, field, value.strip() if value else None)
            # Ignore other fields for security

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete_project(self, project_id: str, current_user: User) -> None:
        """Delete a project if the current user has permission."""
        project = await self.db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        if not self._user_can_access_project(current_user, project):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only delete projects you own"
            )

        await self.db.delete(project)
        await self.db.commit()

    async def _validate_project_key_unique(self, key: str, exclude_id: Optional[str] = None) -> None:
        """Validate project key uniqueness (helper method)."""
        stmt = select(Project).where(func.lower(Project.key) == key.lower())
        if exclude_id:
            stmt = stmt.where(Project.id != exclude_id)

        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project key '{key}' already exists"
            )

    def _user_can_access_project(self, user: User, project: Project) -> bool:
        """Helper to determine if a user can manage a project."""
        if user.role == Role.ADMIN:
            return True
        if user.role == Role.MANAGER and project.owner_id == user.id:
            return True
        return user.id == project.owner_id

    async def get_project_stats(self, project_id: str, user: User) -> dict:
        """Calculate project statistics for dashboards.

        Why service method: Complex aggregation queries.
        Provides useful metrics like issue counts by status.

        Educational Note: This demonstrates advanced SQLAlchemy queries
        with aggregations and grouping for reporting needs.
        """
        # Check access
        project = await self.db.get(Project, project_id)
        if not project or (
            user.role not in [Role.ADMIN, Role.MANAGER] and
            user.id != project.owner_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access project statistics"
            )

        # Aggregate issue counts by status
        from sqlalchemy import func as sql_func
        stmt = select(
            Issue.status,
            sql_func.count(Issue.id).label('count')
        ).where(
            Issue.project_id == project_id
        ).group_by(Issue.status)

        result = await self.db.execute(stmt)
        status_counts = {row.status.value: row.count for row in result}

        # Calculate totals and metrics
        total_issues = sum(status_counts.values())
        completed_issues = status_counts.get(IssueStatus.DONE.value, 0)

        return {
            "project": {
                "id": project.id,
                "key": project.key,
                "name": project.name
            },
            "issues": status_counts,
            "totals": {
                "total": total_issues,
                "completed": completed_issues,
                "completion_rate": completed_issues / total_issues if total_issues > 0 else 0
            }
        }
