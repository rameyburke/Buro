# buro/services/analytics_service.py
#
# Analytics and reporting service for dashboards and metrics.
#
# Educational Notes for Junior Developers:
# - Data aggregation: SQL queries vs application-level processing tradeoffs.
# - Time zones: UTC storage with user timezone conversion.
# - Performance: Index usage and selective queries.
# - Caching: Future optimization for frequently requested reports.

import datetime
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_, desc
import calendar

from buro.models import Issue, Project, User, IssueStatus, IssueType


class AnalyticsService:
    """Service for generating analytics and reports.

    Why separate service: Complex business logic for metrics calculation.
    Reusable across different presentation layers (API, scheduled reports).

    Educational Note: Analytics involve both current snapshots and historical trends.
    Design for both real-time dashboards and periodic reporting.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_project_overview(self, project_id: str) -> Dict[str, Any]:
        """Generate comprehensive project overview metrics.

        Why async: Database queries are the bottleneck, keep them async.
        Returns snapshot of current project state for dashboards.
        """
        # Get project with preloaded relationships would be better in practice
        project = await self.db.get(Project, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Aggregate metrics in optimized queries
        issue_stats = await self._get_issue_status_counts(project_id)
        velocity_metrics = await self._get_velocity_metrics(project_id, days=30)
        aging_issues = await self._get_issues_by_age(project_id)

        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "key": project.key
            },
            "overview": {
                "total_issues": sum(issue_stats.values()),
                "completion_rate": round(
                    issue_stats["done"] / max(sum(issue_stats.values()), 1) * 100, 1
                )
            },
            "issues_by_status": issue_stats,
            "velocity": velocity_metrics,
            "aging": aging_issues
        }

    async def get_team_velocity_report(
        self, team_users: List[User], weeks: int = 12
    ) -> Dict[str, Any]:
        """Calculate team velocity across multiple projects.

        Why team-based: Cross-project metrics for leadership dashboards.
        Supports agile ceremonies like sprint planning and retrospectives.
        """
        # Calculate date range
        now = datetime.datetime.utcnow()
        start_date = now - datetime.timedelta(weeks=weeks)

        team_velocity = {}
        team_user_ids = [str(u.id) for u in team_users]

        for user in team_users:
            # Individual velocity per team member
            personal_velocity = await self._get_user_velocity_metric(
                str(user.id), weeks
            )

            team_velocity[user.full_name] = {
                "completed_issues": personal_velocity,
                "points_completed": personal_velocity,  # Future: story point system
                "avg_completion_time": 0  # Future: time-to-completion metrics
            }

        # Team-level aggregations
        total_completed = sum(v["completed_issues"] for v in team_velocity.values())

        return {
            "period": {
                "weeks": weeks,
                "start_date": start_date.isoformat(),
                "end_date": now.isoformat()
            },
            "team_size": len(team_users),
            "total_completed": total_completed,
            "average_velocity": round(total_completed / max(len(team_users), 1), 1),
            "member_breakdown": team_velocity
        }

    async def get_burndown_chart_data(
        self, project_id: str, issues: List[Issue]
    ) -> Dict[str, Any]:
        """Generate burndown chart data for Kanban projects.

        Why adapted for Kanban: Instead of time-boxed sprints, track cumulative flow.
        Shows how work is progressing over time relative to goals.
        """
        # Simplified burndown for Kanban (focused on work remaining)
        # Real implementation would need: estimation system, target dates

        total_issues = len(issues)
        completed_issues = sum(1 for issue in issues if issue.status == IssueStatus.DONE)

        # Ideal burndown line (linear from total to 0)
        ideal_remaining = list(range(total_issues, 0, -total_issues // max(10, total_issues//2)))
        ideal_remaining.append(0)  # Always end at 0

        # Current actual burndown (simplified)
        actual_remaining = total_issues - completed_issues

        # Create time periods (last 10 work periods)
        time_labels = [f"Period {i+1}" for i in range(len(ideal_remaining))]

        return {
            "labels": time_labels,
            "datasets": [
                {
                    "label": "Ideal Burndown",
                    "data": ideal_remaining,
                    "borderColor": "#3b82f6",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "fill": False
                },
                {
                    "label": "Actual Progress",
                    "data": [total_issues] + [actual_remaining] * (len(time_labels)-1),
                    "borderColor": "#ef4444",
                    "backgroundColor": "rgba(239, 68, 68, 0.1)",
                    "fill": False
                }
            ],
            "summary": {
                "total_issues": total_issues,
                "completed": completed_issues,
                "remaining": actual_remaining,
                "completion_percentage": round(completed_issues / max(total_issues, 1) * 100, 1)
            }
        }

    async def get_issues_aging_report(self, project_ids: List[str]) -> Dict[str, Any]:
        """Analyze how long issues have been in each status.

        Why aging reports: Help identify bottlenecks and stuck work.
        Critical for process improvement and workflow optimization.
        """
        aging_by_status = defaultdict(list)
        aging_summary = {}

        for project_id in project_ids:
            issues = await self._get_issues_with_status_duration(project_id)

            for issue in issues:
                status = issue.status
                days_in_status = (datetime.datetime.utcnow() - issue.updated_at).days

                aging_by_status[status].append({
                    "issue_key": issue.project.generate_issue_key(issue.issue_number),
                    "title": issue.title,
                    "days": days_in_status,
                    "assignee": issue.assignee.full_name if issue.assignee else "Unassigned"
                })

        # Calculate summary statistics
        for status, issues_list in aging_by_status.items():
            if issues_list:
                days_list = [i["days"] for i in issues_list]
                aging_summary[status] = {
                    "issue_count": len(issues_list),
                    "avg_days": round(sum(days_list) / len(days_list), 1),
                    "max_days": max(days_list),
                    "min_days": min(days_list)
                }

        return {
            "aging_by_status": dict(aging_by_status),
            "summary": aging_summary,
            "generated_at": datetime.datetime.utcnow().isoformat()
        }

    # Private helper methods

    async def _get_issue_status_counts(self, project_id: str) -> Dict[str, int]:
        """Count issues by status for a project."""
        stmt = select(Issue.status, func.count(Issue.id)).where(
            Issue.project_id == project_id
        ).group_by(Issue.status)

        result = await self.db.execute(stmt)
        counts = {status.value: count for status, count in result}
        return counts

    async def _get_velocity_metrics(self, project_id: str, days: int) -> Dict[str, Any]:
        """Calculate velocity metrics over specified period."""
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)

        # Issues completed in period
        stmt = select(func.count(Issue.id)).where(
            and_(
                Issue.project_id == project_id,
                Issue.status == IssueStatus.DONE,
                Issue.updated_at >= cutoff_date
            )
        )

        result = await self.db.execute(stmt)
        completed_count = result.scalar_one()

        return {
            "period_days": days,
            "completed_issues": completed_count,
            "daily_average": round(completed_count / days, 2)
        }

    async def _get_user_velocity_metric(self, user_id: str, weeks: int) -> int:
        """Calculate individual user velocity (issues completed)."""
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(weeks=weeks)

        stmt = select(func.count(Issue.id)).where(
            and_(
                Issue.assignee_id == user_id,
                Issue.status == IssueStatus.DONE,
                Issue.updated_at >= cutoff_date
            )
        )

        result = await self.db.execute(stmt)
        return result.scalar_one() or 0

    async def _get_issues_by_age(self, project_id: str) -> Dict[str, Any]:
        """Categorize issues by how long they've been in current status."""
        now = datetime.datetime.utcnow()

        # Get all non-done issues to check aging
        stmt = select(Issue).where(
            and_(
                Issue.project_id == project_id,
                Issue.status != IssueStatus.DONE
            )
        ).order_by(Issue.updated_at.desc())

        result = await self.db.execute(stmt)
        issues = result.scalars().all()

        aging_categories = {
            "fresh": [],      # 0-1 days
            "normal": [],     # 2-3 days
            "aging": [],      # 4-7 days
            "stalled": []     # 8+ days
        }

        for issue in issues:
            days = (now - issue.updated_at).days

            if days <= 1:
                cat = "fresh"
            elif days <= 3:
                cat = "normal"
            elif days <= 7:
                cat = "aging"
            else:
                cat = "stalled"

            aging_categories[cat].append({
                "key": issue.project.generate_issue_key(issue.issue_number),
                "title": issue.title,
                "days": days,
                "status": issue.status.value
            })

        return aging_categories

    async def _get_issues_with_status_duration(self, project_id: str) -> List[Issue]:
        """Helper to get issues with recent status changes."""
        # Simplified implementation - in production would track status change history
        stmt = select(Issue).where(
            Issue.project_id == project_id
        ).order_by(Issue.updated_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())