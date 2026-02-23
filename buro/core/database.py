# buro/core/database.py
#
# Database configuration and session management for SQLAlchemy.
#
# Educational Notes for Junior Developers:
# - SQLAlchemy Engine vs. Connection: Engine manages connection pooling,
#   handles concurrent requests efficiently. Connection is a single database handle.
# - Why async SQLAlchemy: Non-blocking database operations improve performance
#   under concurrent load. Tradeoff: More complex error handling vs. scalability.
# - Dependency Injection pattern: FastAPI's Depends() allows clean separation
#   of concerns and makes testing easier.

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import AsyncGenerator
import os
from os import getenv

# Database URL selection for development/production
# Supports both SQLite (development) and PostgreSQL (production)
_raw_url = getenv("DATABASE_URL", default="sqlite+aiosqlite:///./buro.db")
if _raw_url.startswith("sqlite"):
    # SQLite works fine for development/testing
    DATABASE_URL = _raw_url
else:
    # PostgreSQL for production
    DATABASE_URL = _raw_url.replace("postgresql://", "postgresql+asyncpg://")

# Educational Note: Engine configuration
# - echo=True for development (logs all SQL) helps with debugging
# - poolclass=StaticPool for SQLite testing, not production PostgreSQL
# - Tradeoff: Development visibility vs. production performance overhead
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production to avoid log spam
    future=True,  # Ensures SQLAlchemy 2.0 behavior
    poolclass=StaticPool if DATABASE_URL.startswith("sqlite") else None,
)

# Why sessionmaker with class_=AsyncSession:
# - AsyncSession supports await operations for non-blocking database calls
# - Autocommit/Autoflush: Simplified transaction management
# - Tradeoff: Less granular control over transactions vs. developer convenience
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevents object expiration after commit
)

# Dependency function providing database sessions
# Why this pattern: Ensures session cleanup and proper resource management
# FastAPI calls this for each request, providing clean database access
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function for FastAPI routes.

    Why AsyncGenerator: Allows proper async context management.
    Each request gets a fresh database session.

    Educational Note: This is the Dependency Injection pattern in action.
    - Benefits: Testable, modular, resource-safe
    - Alternative: Global session objects (fragile, hard to test)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # Session automatically closed here due to async context manager
            # Prevents connection leaks in production
            pass