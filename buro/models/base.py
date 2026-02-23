# buro/models/base.py
#
# Base SQLAlchemy model configurations and utilities.
#
# Educational Notes for Junior Developers:
# - DeclarativeBase vs. registred_base(): Modern SQLAlchemy 2.0 approach
#   provides better type annotations and async support.
# - Why CommonBase: Provides consistent ID/timestamp fields across all models.
# - Alternative: Concrete table inheritance (verbose duplication) vs.
#   single table inheritance (limited flexibility).
# - Database compatibility: UUID type handling for different backends.
#   Keep UUID for type safety, use string storage when needed.

from sqlalchemy import String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from uuid import uuid4, UUID
import sqlalchemy as sa

# Why DeclarativeBase over registry approach:
# - Cleaner syntax for common use cases
# - Built-in support for asyncio
# - Tradeoff: Less flexible for complex inheritance vs. standard patterns
class Base(DeclarativeBase):
    """
    Base class for all database models.

    Why UUID primary keys over auto-incrementing integers:
    - Unpredictable IDs prevent enumeration attacks
    - Better for distributed systems (future scalability)
    - Easier data merging across different databases
    - Tradeoff: Slightly slower joins, harder to manually reference in debugging

    Educational Note: UUID v4 (random) chosen over v1 (timestamp-based):
    - No privacy concerns from embedded timestamps
    - Completely random, harder to guess
    - Tradeoff: No temporal ordering vs. potential query optimization
    """

    # Common fields for all tables
    id: Mapped[str] = mapped_column(
        String(36),  # UUID string is 36 characters
        primary_key=True,
        default=lambda: str(uuid4()),
        unique=True,
        index=True,  # Indexed for fast lookups
        comment="Unique identifier using UUID v4 for security and scalability"
    )

    # Timestamp fields for audit trail
    # Why server-side generation with func.now():
    # - Consistent timestamps regardless of client time zones
    # - Trustworthy audit information (can't be spoofed by clients)
    # - Tradeoff: No client-side timestamp control vs. accurate server-side tracking
    created_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Creation timestamp in UTC"
    )

    updated_at: Mapped[sa.DateTime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last modification timestamp in UTC"
    )

    # Note: Each model should define __tablename__ explicitly
    # This avoids issues with foreign key resolution during table creation

    def __repr__(self) -> str:
        """Provide useful string representation for debugging."""
        return f"<{self.__class__.__name__}(id={self.id})>"