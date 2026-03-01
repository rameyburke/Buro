"""Shared pytest fixtures for backend unit tests."""

import asyncio
import os
from typing import Callable, Optional

import pytest
import pytest_asyncio
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from buro.models import (
    Base,
    Issue,
    IssueStatus,
    IssueType,
    Priority,
    Project,
    Role,
    User,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for pytest-asyncio when using session scope."""

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Provide a shared in-memory SQLite engine for async tests."""

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine):
    """Yield a fresh database session with a clean schema for each test."""

    async_session = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def background_tasks():
    """FastAPI BackgroundTasks helper for notification tests."""

    return BackgroundTasks()


@pytest_asyncio.fixture
async def user_factory(db_session) -> Callable[..., User]:
    """Factory fixture to create users with varying roles."""

    async def _factory(
        *,
        email: Optional[str] = None,
        role: Role = Role.DEVELOPER,
        full_name: str = "Test User",
        is_active: bool = True,
        password: str = "secret",
    ) -> User:
        user = User(
            email=email or f"{role.value}-{os.urandom(6).hex()}@example.com",
            full_name=full_name,
            hashed_password=User.hash_password(password),
            role=role,
            is_active=is_active,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _factory


@pytest_asyncio.fixture
async def project_factory(db_session, user_factory) -> Callable[..., Project]:
    """Factory fixture to create projects with owners."""

    async def _factory(
        *,
        owner: Optional[User] = None,
        key: Optional[str] = None,
        name: str = "Test Project",
        description: Optional[str] = "Sample project",
    ) -> Project:
        owner = owner or await user_factory(role=Role.MANAGER)
        project = Project(
            name=name,
            key=(key or f"PRJ{os.urandom(3).hex()}").upper()[:10],
            description=description,
            owner_id=owner.id,
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        return project

    return _factory


@pytest_asyncio.fixture
async def issue_factory(
    db_session,
    project_factory,
    user_factory,
) -> Callable[..., Issue]:
    """Factory fixture to create issues with related entities."""

    async def _factory(
        *,
        project: Optional[Project] = None,
        reporter: Optional[User] = None,
        assignee: Optional[User] = None,
        status: IssueStatus = IssueStatus.BACKLOG,
        issue_type: IssueType = IssueType.TASK,
        priority: Priority = Priority.MEDIUM,
        issue_number: int = 1,
        title: str = "Sample Issue",
    ) -> Issue:
        project = project or await project_factory()
        reporter = reporter or await user_factory(role=Role.MANAGER)
        issue = Issue(
            issue_number=issue_number,
            title=title,
            description="Details",
            issue_type=issue_type,
            status=status,
            priority=priority,
            project_id=project.id,
            reporter_id=reporter.id,
            assignee_id=assignee.id if assignee else None,
        )
        db_session.add(issue)
        await db_session.commit()
        await db_session.refresh(issue)
        # Attach relationship references for convenience
        issue.project = project
        issue.reporter = reporter
        issue.assignee = assignee
        return issue

    return _factory


# Service fixtures ---------------------------------------------------------

@pytest_asyncio.fixture
async def issue_service(db_session):
    from buro.services.issue_service import IssueService

    return IssueService(db_session)


@pytest_asyncio.fixture
async def project_service(db_session):
    from buro.services.project_service import ProjectService

    return ProjectService(db_session)


@pytest_asyncio.fixture
async def analytics_service(db_session):
    from buro.services.analytics_service import AnalyticsService

    return AnalyticsService(db_session)


@pytest_asyncio.fixture
async def auth_service(db_session):
    from buro.services.auth_service import AuthService
    from buro.services.user_service import UserService

    return AuthService(db_session, UserService(db_session))
