"""Unit tests for AnalyticsService data aggregation."""

from datetime import datetime, timedelta

import pytest

from buro.models import IssueStatus, Role


pytestmark = pytest.mark.asyncio


async def test_get_project_overview_summarizes_metrics(
    analytics_service,
    project_factory,
    issue_factory,
):
    project = await project_factory()
    await issue_factory(project=project, status=IssueStatus.BACKLOG, issue_number=1)
    await issue_factory(project=project, status=IssueStatus.DONE, issue_number=2)

    overview = await analytics_service.get_project_overview(project.id)

    assert overview["project"]["id"] == project.id
    assert overview["overview"]["total_issues"] == 2
    assert overview["issues_by_status"][IssueStatus.DONE.value] == 1


async def test_get_team_velocity_report_counts_completed_issues(
    analytics_service,
    issue_factory,
    user_factory,
    project_factory,
):
    project = await project_factory()
    alice = await user_factory(role=Role.DEVELOPER, full_name="Alice")
    bob = await user_factory(role=Role.DEVELOPER, full_name="Bob")

    await issue_factory(project=project, status=IssueStatus.DONE, assignee=alice, issue_number=10)
    await issue_factory(project=project, status=IssueStatus.DONE, assignee=bob, issue_number=11)
    await issue_factory(project=project, status=IssueStatus.DONE, assignee=bob, issue_number=12)

    report = await analytics_service.get_team_velocity_report([alice, bob], weeks=4)

    assert report["total_completed"] == 3
    assert report["member_breakdown"]["Bob"]["completed_issues"] == 2


async def test_get_burndown_chart_data_shapes_datasets(
    analytics_service,
    issue_factory,
):
    issue1 = await issue_factory(status=IssueStatus.BACKLOG, issue_number=20)
    issue2 = await issue_factory(status=IssueStatus.DONE, issue_number=21)

    data = await analytics_service.get_burndown_chart_data(issue1.project_id, [issue1, issue2])

    assert len(data["datasets"]) == 2
    assert data["summary"]["total_issues"] == 2
    assert data["summary"]["completed"] == 1


async def test_get_issues_aging_report_categorizes_by_days(
    analytics_service,
    issue_factory,
    project_factory,
    db_session,
):
    project = await project_factory()
    fresh_issue = await issue_factory(project=project, issue_number=30)
    aging_issue = await issue_factory(project=project, issue_number=31)

    fresh_issue.updated_at = datetime.utcnow() - timedelta(hours=12)
    aging_issue.updated_at = datetime.utcnow() - timedelta(days=5)
    db_session.add_all([fresh_issue, aging_issue])
    await db_session.commit()

    report = await analytics_service.get_issues_aging_report([project.id])

    assert report["aging_by_status"]
    assert any(item["days"] <= 1 for item in report["aging_by_status"][fresh_issue.status])
    assert report["summary"][fresh_issue.status]["issue_count"] >= 1
