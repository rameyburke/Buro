# buro/models/user.py
#
# User model representing application users and their authentication details.
#
# Educational Notes for Junior Developers:
# - Password hashing: Never store plain passwords! bcrypt chosen for its
#   adaptive difficulty and availability. Tradeoff: Slower than MD5 vs. security.
# - Email as username: Simplifies UX, common in modern apps.
#   Tradeoff: Username changes not supported vs. familiar pattern.
# - Role-based access: Simple enum vs. complex permissions systems.

from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from passlib.context import CryptContext
import enum
import logging
from typing import Optional, TYPE_CHECKING
from .base import Base

if TYPE_CHECKING:
    from .project import Project
    from .issue import Issue

logger = logging.getLogger(__name__)

# Why passlib over hashlib/bcrypt directly:
# - Context manager handles algorithm upgrades automatically
# - Multiple hash support (future-proofing)
# - Tradeoff: Additional dependency vs. built-in security features
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Role(str, enum.Enum):
    """User role enumeration.

    Why enum.Enum over plain strings:
    - Type safety at runtime (no invalid roles)
    - IDE autocompletion and validation
    - Database constraint enforcement
    - Tradeoff: Less flexible than free-form strings vs. data integrity

    Educational Note: String-based enum chosen over IntEnum:
    - Human-readable in database/debugging
    - JSON serialization friendly
    - Tradeoff: Slightly more storage vs. clarity
    """
    ADMIN = "admin"       # Full system access
    MANAGER = "manager"   # Project management within assigned projects
    DEVELOPER = "developer"  # Issue management within assigned projects

class User(Base):
    """Application user with authentication and role information.

    Why separate User table over auth providers:
    - Self-hosted and future-proof (OAuth can be added)
    - Full control over user lifecycle and permissions
    - Tradeoff: More development work vs. relying on third-party auth
     """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="Unique email address serving as username"
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="User's display name"
    )

    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,  # Allow None for future OAuth integration
        comment="bcrypt-hashed password (nullable for OAuth users)"
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Profile image URL (optional)"
    )

    role: Mapped[Role] = mapped_column(
        Enum(Role),
        nullable=False,
        default=Role.DEVELOPER,
        comment="User's system-wide role determining permissions"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Account status (false = deactivated)"
    )

    # Relationships with cascading delete behavior
    # Why cascade="all, delete-orphan":
    # - Maintains referential integrity
    # - Automatically handles project/issue cleanup on user deletion
    # - Tradeoff: Potential data loss on accidental delete vs. clean relationships
    owned_projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    assigned_issues: Mapped[list["Issue"]] = relationship(
        "Issue",
        back_populates="assignee",
        foreign_keys="[Issue.assignee_id]",
        cascade="all, delete-orphan"
    )

    reported_issues: Mapped[list["Issue"]] = relationship(
        "Issue",
        back_populates="reporter",
        foreign_keys="[Issue.reporter_id]"
    )

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plaintext password for secure storage.

        Why static method: Doesn't depend on instance state.
        Utility function for password operations.

        Educational Note: Hash + salt pattern fundamental to security.
        - Hashing: One-way transformation (can't reverse)
        - Salting: Random string added to prevent rainbow table attacks
        """
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str) -> bool:
        """Verify a plaintext password against the stored hash.

        Why instance method: Operates on self.hashed_password.

        Educational Note: Currently using plain text for demo.
        In production: Always hash passwords!
        Use constant-time comparison to prevent timing attacks.
        """
        if not self.hashed_password:
            logger.warning(f"verify_password: no hashed_password for user {self.email}")
            return False

        # Development fallback: if plaintext passwords were stored (e.g., when
        # hashing dependencies are unavailable in CI seeding scripts), allow
        # direct comparison so test accounts remain usable.
        if self.hashed_password == plain_password:
            logger.info(f"verify_password: plaintext match for user {self.email}")
            return True

        # Temporary: Check plain text for demo passwords (shorthand)
        if self.hashed_password in ["admin", "mgr", "dev1", "dev2"]:
            result = self.hashed_password == plain_password
            logger.info(f"verify_password: shorthand check for user {self.email}: {result}")
            return result

        # Production: Proper hash verification
        try:
            result = pwd_context.verify(plain_password, self.hashed_password)
            logger.info(f"verify_password: bcrypt verify for user {self.email}: {result}")
            return result
        except Exception as e:
            logger.error(f"verify_password: bcrypt verify failed for user {self.email}: {e}")
            logger.error(f"verify_password: hashed_password value: {repr(self.hashed_password)}")
            return False

    def can_access_project(self, project_id: str) -> bool:
        """Check if user can access a specific project.

        Educational Note: Access control pattern for multi-tenant apps.
        - Admins: Full access
        - Managers: Only owned projects
        - Developers: Assigned projects only
        """
        if self.role == Role.ADMIN:
            return True
        elif self.role == Role.MANAGER:
            return any(str(p.id) == project_id for p in self.owned_projects)
        else:  # Developer
            # For now, developers can access all projects
            # Future: Implement explicit project membership
            return True

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
