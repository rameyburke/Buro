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
from sqlalchemy.orm import joinedload
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

    async def get_project_overview(self, project_id: str, range_label: str) -> Dict[str, Any]:
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
        start_dt, end_dt, dates = self._get_range_window(range_label)
        total_issues = sum(issue_stats.values())

        completed_in_range = await self._count_completed_in_range(project_id, start_dt, end_dt)
        wip_count = await self._count_wip_issues(project_id)
        avg_cycle_time_hours = await self._get_average_cycle_time_hours(
            project_id, start_dt, end_dt
        )
        burndown = await self.get_burndown_chart_data(project_id, range_label)
        burndown_delta = 0
        if burndown["remaining_actual"]:
            burndown_delta = burndown["remaining_actual"][-1] - burndown["remaining_ideal"][-1]

        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "key": project.key
            },
            "overview": {
                "total_issues": total_issues,
                "completed_in_range": completed_in_range,
                "completion_rate": round(
                    completed_in_range / max(total_issues, 1) * 100, 1
                ),
                "wip_count": wip_count,
                "avg_cycle_time_hours": avg_cycle_time_hours,
                "burndown_delta": burndown_delta
            },
            "issues_by_status": issue_stats,
            "range": {
                "label": range_label,
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat(),
                "days": len(dates)
            }
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
        self, project_id: str, range_label: str
    ) -> Dict[str, Any]:
        """Generate burndown chart data for Kanban projects.

        Why adapted for Kanban: Instead of time-boxed sprints, track cumulative flow.
        Shows how work is progressing over time relative to goals.
        """
        # Simplified burndown for Kanban (focused on work remaining)
        # Real implementation would need: estimation system, target dates

        start_dt, end_dt, dates = self._get_range_window(range_label)

        total_stmt = select(func.count(Issue.id)).where(Issue.project_id == project_id)
        total_result = await self.db.execute(total_stmt)
        total_issues = total_result.scalar_one() or 0

        completed_stmt = select(Issue.completed_at).where(
            and_(
                Issue.project_id == project_id,
                Issue.status == IssueStatus.DONE,
                Issue.completed_at.is_not(None),
                Issue.completed_at <= end_dt
            )
        )
        completed_result = await self.db.execute(completed_stmt)
        completed_dates = [row[0].date() for row in completed_result if row[0]]

        completed_by_day = defaultdict(int)
        for completed_date in completed_dates:
            completed_by_day[completed_date] += 1

        cumulative_completed = 0
        remaining_actual = []
        for day in dates:
            cumulative_completed += completed_by_day.get(day, 0)
            remaining_actual.append(max(total_issues - cumulative_completed, 0))

        if len(dates) <= 1:
            remaining_ideal = [total_issues]
        else:
            remaining_ideal = [
                max(int(round(total_issues - (total_issues * i / (len(dates) - 1)))), 0)
                for i in range(len(dates))
            ]

        return {
            "dates": [day.isoformat() for day in dates],
            "remaining_actual": remaining_actual,
            "remaining_ideal": remaining_ideal
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
                status = issue.status.value
                if status == IssueStatus.DONE.value:
                    continue
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
                Issue.completed_at >= cutoff_date
            )
        )

        result = await self.db.execute(stmt)
        completed_count = result.scalar_one() or 0

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
                Issue.completed_at >= cutoff_date
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

    def _get_range_window(
        self, range_label: str
    ) -> Tuple[datetime.datetime, datetime.datetime, List[datetime.date]]:
        days = self._range_to_days(range_label)
        end_date = datetime.datetime.utcnow().date()
        start_date = end_date - datetime.timedelta(days=days - 1)

        dates = [start_date + datetime.timedelta(days=i) for i in range(days)]
        start_dt = datetime.datetime.combine(start_date, datetime.time.min)
        end_dt = datetime.datetime.combine(end_date, datetime.time.max)

        return start_dt, end_dt, dates

    def _range_to_days(self, range_label: str) -> int:
        options = {
            "7d": 7,
            "14d": 14,
            "30d": 30,
            "90d": 90
        }
        return options.get(range_label, 30)

    async def _count_completed_in_range(
        self, project_id: str, start_dt: datetime.datetime, end_dt: datetime.datetime
    ) -> int:
        stmt = select(func.count(Issue.id)).where(
            and_(
                Issue.project_id == project_id,
                Issue.status == IssueStatus.DONE,
                Issue.completed_at.is_not(None),
                Issue.completed_at >= start_dt,
                Issue.completed_at <= end_dt
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one() or 0

    async def _count_wip_issues(self, project_id: str) -> int:
        status_values = {IssueStatus.IN_PROGRESS.value, "review"}

        stmt = select(func.count(Issue.id)).where(
            and_(
                Issue.project_id == project_id,
                Issue.status.in_(status_values)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one() or 0

    async def _get_average_cycle_time_hours(
        self, project_id: str, start_dt: datetime.datetime, end_dt: datetime.datetime
    ) -> float:
        stmt = select(Issue.started_at, Issue.completed_at).where(
            and_(
                Issue.project_id == project_id,
                Issue.completed_at.is_not(None),
                Issue.started_at.is_not(None),
                Issue.completed_at >= start_dt,
                Issue.completed_at <= end_dt
            )
        )
        result = await self.db.execute(stmt)
        durations = []
        for started_at, completed_at in result:
            if started_at and completed_at:
                duration = completed_at - started_at
                durations.append(duration.total_seconds() / 3600)

        if not durations:
            return 0.0
        return round(sum(durations) / len(durations), 1)

    async def get_cycle_time_trend(
        self, project_id: str, range_label: str
    ) -> Dict[str, Any]:
        start_dt, end_dt, dates = self._get_range_window(range_label)

        stmt = select(Issue.started_at, Issue.completed_at).where(
            and_(
                Issue.project_id == project_id,
                Issue.completed_at.is_not(None),
                Issue.started_at.is_not(None),
                Issue.completed_at >= start_dt,
                Issue.completed_at <= end_dt
            )
        )

        result = await self.db.execute(stmt)
        durations_by_day: Dict[datetime.date, List[float]] = defaultdict(list)
        for started_at, completed_at in result:
            if started_at and completed_at:
                day = completed_at.date()
                duration_hours = (completed_at - started_at).total_seconds() / 3600
                durations_by_day[day].append(duration_hours)

        avg_series = []
        for day in dates:
            values = durations_by_day.get(day, [])
            if values:
                avg_series.append(round(sum(values) / len(values), 1))
            else:
                avg_series.append(None)

        return {
            "dates": [day.isoformat() for day in dates],
            "avg_cycle_time_hours": avg_series
        }

    async def get_throughput(self, project_id: str, range_label: str) -> Dict[str, Any]:
        start_dt, end_dt, dates = self._get_range_window(range_label)

        stmt = select(Issue.completed_at).where(
            and_(
                Issue.project_id == project_id,
                Issue.status == IssueStatus.DONE,
                Issue.completed_at.is_not(None),
                Issue.completed_at >= start_dt,
                Issue.completed_at <= end_dt
            )
        )
        result = await self.db.execute(stmt)
        counts_by_day = defaultdict(int)
        for (completed_at,) in result:
            if completed_at:
                counts_by_day[completed_at.date()] += 1

        counts_series = [counts_by_day.get(day, 0) for day in dates]

        return {
            "dates": [day.isoformat() for day in dates],
            "completed_counts": counts_series
        }

    async def get_aging_summary(self, project_id: str) -> Dict[str, Any]:
        now = datetime.datetime.utcnow()
        stmt = select(Issue.status, Issue.updated_at).where(
            and_(
                Issue.project_id == project_id,
                Issue.status != IssueStatus.DONE
            )
        )
        result = await self.db.execute(stmt)

        summary: Dict[str, Dict[str, float]] = {}
        buckets: Dict[str, List[int]] = defaultdict(list)
        for status, updated_at in result:
            if updated_at:
                buckets[status.value].append((now - updated_at).days)

        for status, days_list in buckets.items():
            if days_list:
                summary[status] = {
                    "count": len(days_list),
                    "avg_age_days": round(sum(days_list) / len(days_list), 1),
                    "max_age_days": max(days_list)
                }

        return {
            "status_breakdown": summary,
            "generated_at": now.isoformat()
        }

    async def get_oldest_open_issues(self, project_id: str, limit: int) -> Dict[str, Any]:
        stmt = select(Issue).options(
            joinedload(Issue.project),
            joinedload(Issue.assignee)
        ).where(
            and_(
                Issue.project_id == project_id,
                Issue.status != IssueStatus.DONE
            )
        ).order_by(Issue.created_at.asc()).limit(limit)

        result = await self.db.execute(stmt)
        issues = list(result.scalars().all())

        now = datetime.datetime.utcnow()
        oldest = []
        for issue in issues:
            age_days = (now - issue.created_at).days if issue.created_at else 0
            oldest.append({
                "key": issue.project.generate_issue_key(issue.issue_number)
                if issue.project else f"UNKNOWN-{issue.issue_number}",
                "title": issue.title,
                "assignee": issue.assignee.full_name if issue.assignee else "Unassigned",
                "status": issue.status.value,
                "age_days": age_days
            })

        return {
            "issues": oldest,
            "generated_at": now.isoformat()
        }

    async def get_workload_distribution(self, project_id: str) -> Dict[str, Any]:
        stmt = select(Issue.assignee_id, Issue.status, func.count(Issue.id)).where(
            and_(
                Issue.project_id == project_id,
                Issue.status != IssueStatus.DONE
            )
        ).group_by(Issue.assignee_id, Issue.status)

        result = await self.db.execute(stmt)
        workload: Dict[str, Dict[str, Any]] = {}
        for assignee_id, status, count in result:
            key = assignee_id or "unassigned"
            if key not in workload:
                workload[key] = {
                    "user_id": assignee_id,
                    "user_name": "Unassigned",
                    "status_counts": {},
                    "wip_total": 0,
                    "total_active": 0
                }

            workload[key]["status_counts"][status.value] = count
            workload[key]["total_active"] += count
            if status.value in {IssueStatus.IN_PROGRESS.value, "review"}:
                workload[key]["wip_total"] += count

        # Resolve user names
        for item in workload.values():
            if item["user_id"]:
                user = await self.db.get(User, item["user_id"])
                if user:
                    item["user_name"] = user.full_name

        return {
            "assignees": sorted(
                workload.values(), key=lambda x: x["wip_total"], reverse=True
            )
        }
