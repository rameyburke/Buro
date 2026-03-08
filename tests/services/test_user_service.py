"""Unit tests for UserService admin maintenance workflows."""

import pytest
from fastapi import HTTPException

from buro.models import Role
from buro.services.user_service import UserService


pytestmark = pytest.mark.asyncio


async def test_create_user_generates_temp_password(db_session, user_factory):
    service = UserService(db_session)
    admin = await user_factory(role=Role.ADMIN)

    created_user, temp_password = await service.create_user(
        email="new.user@example.com",
        full_name="New User",
        role=Role.DEVELOPER,
        current_user=admin,
    )

    assert created_user.email == "new.user@example.com"
    assert created_user.role == Role.DEVELOPER
    assert created_user.verify_password(temp_password) is True
    assert len(temp_password) == 12


async def test_create_user_rejects_non_admin(db_session, user_factory):
    service = UserService(db_session)
    manager = await user_factory(role=Role.MANAGER)

    with pytest.raises(HTTPException) as exc:
        await service.create_user(
            email="blocked@example.com",
            full_name="Blocked User",
            role=Role.DEVELOPER,
            current_user=manager,
        )

    assert exc.value.status_code == 403


async def test_get_users_hides_inactive_by_default(db_session, user_factory):
    service = UserService(db_session)
    admin = await user_factory(role=Role.ADMIN)
    await user_factory(role=Role.DEVELOPER, full_name="Active User", is_active=True)
    await user_factory(role=Role.DEVELOPER, full_name="Inactive User", is_active=False)

    active_only_users, active_only_total = await service.get_users(current_user=admin)
    all_users, all_total = await service.get_users(current_user=admin, include_inactive=True)

    assert all(user.is_active for user in active_only_users)
    assert active_only_total < all_total
    assert any(not user.is_active for user in all_users)


async def test_deactivate_user_sets_account_inactive(db_session, user_factory):
    service = UserService(db_session)
    admin = await user_factory(role=Role.ADMIN)
    target = await user_factory(role=Role.DEVELOPER, is_active=True)

    await service.deactivate_user(target.id, admin)
    refreshed_target = await service.get_user_by_id(target.id)

    assert refreshed_target.is_active is False
