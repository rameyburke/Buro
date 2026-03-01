"""Unit tests for Issue model helper properties and methods."""

import pytest

from buro.models import IssueStatus


pytestmark = pytest.mark.asyncio


async def test_issue_key_uses_project_prefix(issue_factory, project_factory):
    project = await project_factory(key="ABC")
    issue = await issue_factory(project=project, issue_number=7)

    assert issue.key == "ABC-7"


async def test_is_resolved_matches_done_status(issue_factory):
    issue = await issue_factory(status=IssueStatus.DONE)

    assert issue.is_resolved is True


async def test_transition_status_allows_forward_only(issue_factory):
    issue = await issue_factory(status=IssueStatus.TO_DO)

    assert issue.transition_status(IssueStatus.IN_PROGRESS) is True
    assert issue.status == IssueStatus.IN_PROGRESS

    # reverse transition should fail, except to DONE
    assert issue.transition_status(IssueStatus.TO_DO) is False
    assert issue.status == IssueStatus.IN_PROGRESS

    assert issue.transition_status(IssueStatus.DONE) is True


async def test_can_be_assigned_to_returns_true(issue_factory):
    issue = await issue_factory()

    assert issue.can_be_assigned_to("any-user-id") is True
