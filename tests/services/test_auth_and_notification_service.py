"""Unit tests for authentication and notification services."""

import pytest
from fastapi import HTTPException, BackgroundTasks

from buro.models import Role
from buro.services.notification_service import EmailNotificationService


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# AuthService tests
# ---------------------------------------------------------------------------


async def test_authenticate_user_with_valid_credentials(auth_service, user_factory):
    user = await user_factory(email="admin@example.com", password="s3cret", role=Role.ADMIN)

    authenticated = await auth_service.authenticate_user("admin@example.com", "s3cret")

    assert authenticated.id == user.id


async def test_authenticate_user_invalid_password(auth_service, user_factory):
    await user_factory(email="user@example.com", password="goodpass")

    with pytest.raises(HTTPException) as exc:
        await auth_service.authenticate_user("user@example.com", "badpass")

    assert exc.value.status_code == 401


async def test_register_user_prevents_duplicates(auth_service):
    await auth_service.register_user(
        email="dup@example.com",
        full_name="Dup User",
        password="pass",
    )

    with pytest.raises(HTTPException) as exc:
        await auth_service.register_user(
            email="dup@example.com",
            full_name="Dup User",
            password="pass",
        )

    assert exc.value.status_code == 409


async def test_authorize_admin_or_manager(auth_service, user_factory):
    admin = await user_factory(role=Role.ADMIN, email="admin@ex.com")
    manager = await user_factory(role=Role.MANAGER, email="mgr@ex.com")
    developer = await user_factory(role=Role.DEVELOPER, email="dev@ex.com")

    await auth_service.authorize_admin_or_manager(admin)  # should not raise
    await auth_service.authorize_admin_or_manager(manager)

    with pytest.raises(HTTPException):
        await auth_service.authorize_admin_or_manager(developer)


async def test_create_user_token_contains_payload(auth_service, user_factory):
    user = await user_factory(email="token@example.com")

    token = await auth_service.create_user_token(user)

    assert "access_token" in token
    assert token["user"]["email"] == "token@example.com"


# ---------------------------------------------------------------------------
# Notification service tests
# ---------------------------------------------------------------------------


async def test_issue_assignment_notification_skips_when_disabled(
    issue_factory,
    user_factory,
    monkeypatch,
):
    monkeypatch.delenv("ENABLE_EMAIL_NOTIFICATIONS", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)

    service = EmailNotificationService()
    issue = await issue_factory()
    assignee = await user_factory(email="notify@example.com")
    tasks = BackgroundTasks()

    await service.send_issue_assigned_notification(tasks, issue, assignee)

    assert tasks.tasks == []


async def test_issue_assignment_notification_enqueues_task_when_enabled(
    issue_factory,
    user_factory,
    monkeypatch,
):
    monkeypatch.setenv("ENABLE_EMAIL_NOTIFICATIONS", "true")
    monkeypatch.setenv("SMTP_USERNAME", "user")
    monkeypatch.setenv("SMTP_PASSWORD", "pass")
    monkeypatch.setenv("FROM_EMAIL", "noreply@example.com")

    service = EmailNotificationService()

    async def fake_send_email(*args, **kwargs):
        return None

    # Replace network call with stub
    service._send_email = fake_send_email  # type: ignore[attr-defined]

    issue = await issue_factory()
    assignee = await user_factory(email="notify-enabled@example.com")
    tasks = BackgroundTasks()

    await service.send_issue_assigned_notification(tasks, issue, assignee)

    assert len(tasks.tasks) == 1
