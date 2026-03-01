"""Unit tests for ProjectService operations."""

import pytest
from fastapi import HTTPException

from buro.models import IssueStatus, Role, Project


pytestmark = pytest.mark.asyncio


async def test_create_project_allows_managers(project_service, user_factory):
    manager = await user_factory(role=Role.MANAGER)

    project = await project_service.create_project(
        name="Alpha",
        key="ALPHA",
        description="First project",
        owner=manager,
    )

    assert project.owner_id == manager.id
    assert project.key == "ALPHA"


async def test_create_project_rejects_developers(project_service, user_factory):
    developer = await user_factory(role=Role.DEVELOPER)

    with pytest.raises(HTTPException) as exc:
        await project_service.create_project(
            name="Beta",
            key="BETA",
            description=None,
            owner=developer,
        )

    assert exc.value.status_code == 403


async def test_create_project_prevents_duplicate_keys(project_service, user_factory):
    manager = await user_factory(role=Role.MANAGER)
    await project_service.create_project(
        name="Gamma",
        key="DUP",
        description=None,
        owner=manager,
    )

    with pytest.raises(HTTPException) as exc:
        await project_service.create_project(
            name="Gamma Copy",
            key="dup",  # lower-case to ensure case-insensitive uniqueness
            description=None,
            owner=manager,
        )

    assert exc.value.status_code == 409


async def test_update_project_changes_name_and_key(
    project_service,
    project_factory,
    user_factory,
):
    manager = await user_factory(role=Role.MANAGER)
    project = await project_factory(owner=manager, key="PRJ1", name="Original")

    updated = await project_service.update_project(
        project.id,
        {"name": "Updated", "key": "NEWKEY"},
        current_user=manager,
    )

    assert updated.name == "Updated"
    assert updated.key == "NEWKEY"


async def test_update_project_requires_ownership(
    project_service,
    project_factory,
    user_factory,
):
    owner = await user_factory(role=Role.MANAGER)
    other_user = await user_factory(role=Role.MANAGER)
    project = await project_factory(owner=owner, key="OWNED")

    with pytest.raises(HTTPException) as exc:
        await project_service.update_project(
            project.id,
            {"name": "Hacked"},
            current_user=other_user,
        )

    assert exc.value.status_code == 403


async def test_delete_project_removes_record(
    project_service,
    project_factory,
    user_factory,
    db_session,
):
    owner = await user_factory(role=Role.MANAGER)
    project = await project_factory(owner=owner)

    await project_service.delete_project(project.id, current_user=owner)

    assert await db_session.get(Project, project.id) is None


async def test_get_project_stats_returns_issue_counts(
    project_service,
    project_factory,
    issue_factory,
    user_factory,
):
    owner = await user_factory(role=Role.MANAGER)
    project = await project_factory(owner=owner)
    await issue_factory(project=project, status=IssueStatus.BACKLOG, issue_number=1)
    await issue_factory(project=project, status=IssueStatus.DONE, issue_number=2)
    await issue_factory(project=project, status=IssueStatus.DONE, issue_number=3)

    stats = await project_service.get_project_stats(project.id, user=owner)

    assert stats["project"]["id"] == project.id
    assert stats["totals"]["total"] == 3
    assert stats["issues"][IssueStatus.DONE.value] == 2
