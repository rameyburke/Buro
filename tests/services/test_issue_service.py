"""Unit tests for IssueService business logic."""

import pytest
from fastapi import HTTPException

from buro.models import IssueStatus, IssueType, Priority, Role, Issue


pytestmark = pytest.mark.asyncio


async def test_create_issue_generates_sequential_numbers(
    issue_service,
    project_factory,
    user_factory,
):
    project = await project_factory()
    reporter = await user_factory(role=Role.MANAGER)

    first_issue = await issue_service.create_issue(
        title="First",
        description="",
        issue_type=IssueType.TASK,
        priority=Priority.MEDIUM,
        project_id=project.id,
        reporter=reporter,
    )

    second_issue = await issue_service.create_issue(
        title="Second",
        description="",
        issue_type=IssueType.BUG,
        priority=Priority.HIGH,
        project_id=project.id,
        reporter=reporter,
    )

    assert first_issue.issue_number == 1
    assert second_issue.issue_number == 2


async def test_create_issue_missing_project_raises(issue_service, user_factory):
    reporter = await user_factory(role=Role.MANAGER)

    with pytest.raises(HTTPException) as exc:
        await issue_service.create_issue(
            title="Orphan",
            description=None,
            issue_type=IssueType.TASK,
            priority=Priority.MEDIUM,
            project_id="non-existent",
            reporter=reporter,
        )

    assert exc.value.status_code == 404


async def test_create_issue_invalid_assignee(issue_service, project_factory, user_factory):
    project = await project_factory()
    reporter = await user_factory(role=Role.MANAGER)
    inactive_user = await user_factory(is_active=False)

    with pytest.raises(HTTPException) as exc:
        await issue_service.create_issue(
            title="Unassignable",
            description=None,
            issue_type=IssueType.BUG,
            priority=Priority.LOW,
            project_id=project.id,
            reporter=reporter,
            assignee_id=inactive_user.id,
        )

    assert exc.value.status_code == 400


async def test_get_issue_by_key_returns_issue(
    issue_service,
    project_factory,
    user_factory,
):
    project = await project_factory(key="KANBAN")
    reporter = await user_factory(role=Role.MANAGER)

    created_issue = await issue_service.create_issue(
        title="Lookup",
        description="",
        issue_type=IssueType.TASK,
        priority=Priority.MEDIUM,
        project_id=project.id,
        reporter=reporter,
    )

    fetched_issue = await issue_service.get_issue_by_key(project.key, created_issue.issue_number)
    assert fetched_issue.id == created_issue.id


async def test_list_issues_supports_status_filter(
    issue_service,
    issue_factory,
    project_factory,
    user_factory,
):
    project = await project_factory()
    reporter = await user_factory(role=Role.MANAGER)
    await issue_factory(project=project, status=IssueStatus.BACKLOG, issue_number=10)
    await issue_factory(project=project, status=IssueStatus.IN_PROGRESS, issue_number=11)

    results = await issue_service.list_issues(
        project_id=project.id,
        status=IssueStatus.IN_PROGRESS,
        current_user=reporter,
    )

    assert len(results) == 1
    assert results[0].status == IssueStatus.IN_PROGRESS


async def test_update_issue_changes_fields_and_status(
    issue_service,
    issue_factory,
    user_factory,
    background_tasks,
):
    assignee = await user_factory(role=Role.DEVELOPER)
    issue = await issue_factory()
    reporter = issue.reporter

    updates = {
        "title": "Updated title",
        "description": "Updated description",
        "priority": Priority.HIGH.value,
        "assignee_id": assignee.id,
        "status": IssueStatus.DONE.value,
    }

    updated_issue = await issue_service.update_issue(
        issue.id,
        updates,
        current_user=reporter,
        background_tasks=background_tasks,
    )

    assert updated_issue.title == "Updated title"
    assert updated_issue.description == "Updated description"
    assert updated_issue.priority == Priority.HIGH
    assert updated_issue.assignee_id == assignee.id
    assert updated_issue.status == IssueStatus.DONE


async def test_update_issue_validates_required_fields(issue_service, issue_factory):
    issue = await issue_factory()

    with pytest.raises(HTTPException) as exc:
        await issue_service.update_issue(
            issue.id,
            {"title": "   "},
            current_user=issue.reporter,
        )

    assert exc.value.status_code == 400


async def test_delete_issue_removes_record(issue_service, issue_factory, db_session):
    issue = await issue_factory()

    await issue_service.delete_issue(issue.id, current_user=issue.reporter)

    assert await db_session.get(Issue, issue.id) is None
