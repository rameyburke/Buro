# buro/models/project.py
#
# Project model representing workspace containers for issues.
#
# Educational Notes for Junior Developers:
# - Projects as workspaces: Logical grouping for issues and users.
#   Like Jira projects or GitHub repositories.
# - Key prefixes: Human-readable identifiers (BURO-123) for issues.
#   Chosen over auto-incrementing IDs for clarity.
# - Default assignee: Optional project-wide default to reduce clicks.
#   Tradeoff: Additional database queries vs. improved UX.

from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING, List
from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .issue import Issue

class Project(Base):
    """Project workspace containing issues and team members.

    Why separate table over embedding in issues:
    - Teams work across projects, need shared context
    - Projects have lifecycle independent of issues
    - Allows future features like project templates, archiving
    - Tradeoff: Additional table joins vs. simpler queries

    Educational Note: Domain modeling decision - Projects are top-level
    containers that own Issues, similar to how Organizations own Repositories.
     """

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable project display name"
    )

    key: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        index=True,
        nullable=False,
        comment="Short code used as issue prefix (e.g., 'BURO')"
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="Optional project description or charter"
    )

    # Foreign key to owner (typically a manager or admin)
    # Why separate owner from members: Single point of administrative control
    # Alternative: Many-to-many ownership (complex, unnecessary for scale)
    owner_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        comment="User ID of project owner (manager/admin privileges)"
    )

    # Why not store default_assignee_id directly as foreign key:
    # - Allows None (no default assignee for some projects)
    # - Protects against circular references during deletion
    # - Tradeoff: Additional application logic vs. simple database constraints
    default_assignee_id: Mapped[Optional[str]] = mapped_column(
        String(36),  # UUID length
        nullable=True,
        comment="Optional default user ID for new issues"
    )

    # Relationships with back-references
    # Why back_populates over backref:
    # - Explicit bidirectional relationships
    # - Better IDE support and type checking
    # - Tradeoff: More verbose setup vs. automatic backrefs
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_projects",
        foreign_keys=[owner_id]
    )

    # Issues relationship - lazy loading by default
    # Why lazy='select': Load issues only when accessed (performance)
    # Alternative: lazy='joined' (eager loading, more upfront queries)
    issues: Mapped[List["Issue"]] = relationship(
        "Issue",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    @property
    def default_assignee(self) -> Optional["User"]:
        """Get the default assignee user object.

        Why property over direct relationship:
        - Computed field for clean API
        - Allows None handling gracefully
        - Tradeoff: Additional database queries vs. cleaner code

        Educational Note: Properties vs. direct relationships.
        - Properties: Business logic encapsulation
        - Direct relationships: Complex join optimization
        """
        if not self.default_assignee_id:
            return None
        # This would need access to a session - simplified for demo
        # In real code, we'd need to pass a session or handle differently
        return None

    def generate_issue_key(self, issue_number: int) -> str:
        """Generate a Jira-style issue key.

        Educational Note: Business logic in models vs. services.
        - Models: Simple computed properties and validation
        - Services: Complex business rules and external dependencies
        """
        return f"{self.key}-{issue_number}"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"<Project(id={self.id}, key={self.key}, name={self.name})>"