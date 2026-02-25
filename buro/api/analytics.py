# buro/api/analytics.py
#
# Analytics and reporting API endpoints.
#
# Educational Notes for Junior Developers:
# - Read-heavy endpoints: Analytics involves complex queries, optimize for reads.
# - Caching: Future consideration for expensive calculations.
# - Data format: Chart libraries expect specific JSON structures.
# - Security: Analytics often contain sensitive project data.

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from buro.core.database import get_db
from buro.models import User, Project, Role
from buro.api.auth import get_current_user
from buro.services.project_service import ProjectService
from buro.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/projects/{project_id}/overview")
async def get_project_overview(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive project overview with metrics.

    Why GET endpoint: Analytics are read-heavy, idempotent operations.
    Provides dashboard data without requiring full project metadata.

    Educational Note: This endpoint aggregates multiple metrics:
    - Status distribution for visual charts
    - Velocity trends for performance tracking
    - Aging analysis for process optimization
    """
    # Check access permissions
    project_service = ProjectService(db)

    try:
        # User must have access to this project
        project = await project_service.db.get(Project, project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Check access (project owner or admin)
        if (current_user.role != Role.ADMIN and
            current_user.id != project.owner_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to project analytics"
            )

    except HTTPException:
        raise

    analytics_service = AnalyticsService(db)
    overview = await analytics_service.get_project_overview(project_id)

    return overview

@router.get("/projects/{project_id}/burndown")
async def get_burndown_chart(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get burndown chart data for Kanban projects.

    Why separate endpoint: Burndown algorithms are complex and specialized.
    Allows different implementations for Scrum vs Kanban.

    Educational Note: Burndown charts show work remaining over time.
    Kanban version: Tracks towards completion goals rather than sprint deadlines.
    """
    # Access control same as project overview
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    if (current_user.role != Role.ADMIN and
        current_user.id not in [project.owner_id]):  # Future: team membership
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to project analytics"
        )

    # Get issues for burndown calculation
    from buro.services.issue_service import IssueService
    issue_service = IssueService(db)
    issues = await issue_service.list_issues(project_id=project_id)

    analytics_service = AnalyticsService(db)
    burndown_data = await analytics_service.get_burndown_chart_data(
        project_id, issues
    )

    return burndown_data

@router.get("/velocity/{user_id}")
async def get_user_velocity(
    user_id: str,
    weeks: Optional[int] = 4,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get individual user velocity metrics.

    Why user_id parameter: Allows viewing different team members' velocities.
    Supports agile ceremonies and performance discussions.

    Educational Note: Velocity shows throughput, not natural productivity.
    Individual metrics can be sensitive - careful with privacy considerations.
    """
    # Permission: Users can view their own velocity, admins can view all
    if (current_user.id != user_id and current_user.role != Role.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view own velocity metrics"
        )

    # Verify user exists
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    analytics_service = AnalyticsService(db)
    velocity = await analytics_service._get_user_velocity_metric(user_id, weeks or 4)

    return {
        "user_id": user_id,
        "user_name": target_user.full_name,
        "period_weeks": weeks,
        "completed_issues": velocity
    }

@router.get("/team/velocity")
async def get_team_velocity(
    weeks: Optional[int] = 4,
    project_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get team velocity metrics across projects.

    Why optional project filter: Allows team-level view or project-specific.
    Supports leadership dashboards and release planning.

    Educational Note: Team velocity is more useful than individual velocity.
    Avoids developer competition and focuses on collective delivery.
    """
    # For now, get all users (simplified team)
    # Future: Implement proper team/project membership
    from sqlalchemy import select
    from buro.models import User

    if current_user.role == Role.ADMIN:
        # Admins can see all users
        users_result = await db.execute(select(User))
        team_users = list(users_result.scalars().all())
    else:
        # Non-admins can only see themselves for now
        # Future: Show team members based on project membership
        team_users = [current_user]

    analytics_service = AnalyticsService(db)
    velocity_report = await analytics_service.get_team_velocity_report(
        team_users, weeks or 4
    )

    return velocity_report

@router.get("/issues/aging")
async def get_issues_aging_report(
    project_ids: Optional[str] = None,
    max_age_days: Optional[int] = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get issues aging report to identify bottlenecks.

    Why aging reports: Critical for process improvement.
    Shows which issues have been stuck too long in workflow.

    Educational Note: Aging analysis answers:
    - Are issues getting stuck? Where?
    - What's the average time in each status?
    - Which assignees have the oldest issues?
    """
    # Parse project_ids (comma-separated)
    if project_ids:
        project_list = [pid.strip() for pid in project_ids.split(",")]
    else:
        # Default to current user's projects
        project_service = ProjectService(db)
        user_projects = await project_service.list_user_projects(current_user)
        project_list = [p.id for p in user_projects]

    analytics_service = AnalyticsService(db)
    aging_report = await analytics_service.get_issues_aging_report(project_list)

    return aging_report

# Future endpoints to consider:
# - POST /reports/{report_id}/export - Export reports to PDF/Excel
# - GET /dashboard - Combined dashboard data
# - POST /analytics/cache/invalidate - Manual cache invalidation

@router.get("/issues/workload")
async def get_workload_distribution(
    project_ids: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workload distribution across team members.

    Why workload reports: Help identify imbalances and support work planning.
    Shows issue counts by assignee and priority.

    Educational Note: Workload balancing is key to agile delivery:
    - Too much work = burnt-out developers
    - Too little work = inefficient resource use
    """
    # Parse projects
    if project_ids:
        project_list = [pid.strip() for pid in project_ids.split(",")]
    else:
        project_service = ProjectService(db)
        user_projects = await project_service.list_user_projects(current_user)
        project_list = [p.id for p in user_projects]

    # Get assignee distribution
    from sqlalchemy import select, func
    from buro.models import Issue

    # Query to count issues by assignee
    stmt = select(
        Issue.assignee_id,
        Issue.priority,
        func.count(Issue.id).label('count')
    ).where(
        Issue.project_id.in_(project_list) if project_list else True,
        Issue.status != Issue.status.DONE  # Only active work
    ).group_by(
        Issue.assignee_id,
        Issue.priority
    )

    results = await db.execute(stmt)

    # Process results into workload structure
    workload = {}
    priorities = {'highest': 4, 'high': 3, 'medium': 2, 'low': 1, 'lowest': 0}

    for row in results:
        assignee_id = row.assignee_id
        priority = row.priority
        count = row.count

        if assignee_id not in workload:
            workload[assignee_id] = {
                'user_id': assignee_id,
                'total_issues': 0,
                'by_priority': {},
                'workload_score': 0  # Simple scoring: issue count * priority weight
            }

        workload[assignee_id]['total_issues'] += count
        workload[assignee_id]['by_priority'][priority] = count
        workload[assignee_id]['workload_score'] += count * priorities.get(priority, 1)

    # Add user names (resolve IDs to names)
    final_workload = []
    for item in workload.values():
        user = await db.get(User, item['user_id'])
        if user:
            final_workload.append({
                **item,
                'user_name': user.full_name,
                'user_email': user.email
            })

    # Sort by total workload descending
    final_workload.sort(key=lambda x: x['workload_score'], reverse=True)

    return {
        "workload_distribution": final_workload,
        "metadata": {
            "project_ids": project_list,
            "generated_at": "2026-02-23T08:38:35Z",
            "status_filter": "active (non-done)"
        }
    }