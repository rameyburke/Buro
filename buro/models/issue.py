# buro/models/issue.py
#
# Issue model representing work items in the agile system.
#
# Educational Notes for Junior Developers:
# - Issue types: Unified approach with extensible type field vs.
#   separate tables (chosen for simplicity and query flexibility).
# - Polymorphic behavior: Single table handles all issue types.
#   Tradeoff: Some fields unused by certain types vs. simpler schema.
# - Status progression: Simple linear workflow vs. complex state machines.
#   Agile boards typically use linear progression for clarity.

from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING, List
import enum

from .base import Base

if TYPE_CHECKING:
    from .user import User
    from .project import Project

class IssueType(str, enum.Enum):
    """Types of issues supported in the agile system.

    Why enum over plain strings:
    - Compile-time type safety (IDE catches invalid types)
    - Database constraints prevent invalid data
    - Extensible without breaking existing code
    - Tradeoff: Less flexible than free-form vs. data integrity

    Educational Note: These correspond to Jira's issue types:
    - BUG: Software defects requiring fixes
    - TASK: General work items, chores, or improvements
    - STORY: User-facing features (user stories)
    - EPIC: Large features containing multiple stories
    """
    BUG = "bug"
    TASK = "task"
    STORY = "story"
    EPIC = "epic"

class IssueStatus(str, enum.Enum):
    """Kanban workflow states for issues.

    Why simple status enum vs. complex workflow engine:
    - Matches typical agile team's needs
    - Simplicity allows future customization
    - Tradeoff: Less flexible workflows vs. easier implementation

    Educational Note: Kanban focuses on work visualization over time,
    unlike Scrum's time-boxed sprints. These states are minimal viable workflow.
    """
    BACKLOG = "backlog"      # Not yet started
    TO_DO = "to_do"         # Ready to work on
    IN_PROGRESS = "in_progress"  # Currently being worked
    DONE = "done"          # Completed/closed

class Priority(str, enum.Enum):
    """Issue priority levels for work prioritization.

    Why enum over numeric scale (1-5):
    - Self-documenting ("highest" clearer than 1)
    - Prevents invalid values at runtime
    - Matches typical negative language use
    - Tradeoff: Limited granularity vs. explicit values and labels
    """
    HIGHEST = "highest"    # Blocker/critical issue
    HIGH = "high"         # Important but not blocking
    MEDIUM = "medium"     # Normal priority (default)
    LOW = "low"          # Nice-to-have, low urgency
    LOWEST = "lowest"    # Trivial improvements

class Issue(Base):
    __tablename__ = "issues"

    """Core work item representing Epics, Stories, Tasks, or Bugs.

    Why single table inheritance vs. separate tables:
    - Query all issue types together (useful for search, reporting)
    - Polymorphic relationships work naturally
    - Easier migrations and schema evolution
    - Tradeoff: NULL columns for type-specific fields vs. schema simplicity

    Educational Note: Domain modeling decision - Issues are the atomic
    unit of work. Everything else (projects, users) exists to support issues.
    """
    # Store issue number for key generation (e.g., issue #123 in project)
    # Why not auto-incrementing: Project-scoped numbering.
    # Each project maintains its own sequence for human-readable keys.
    issue_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential number within project (1,2,3...) for key generation"
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Brief, descriptive title of the issue"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description, requirements, or steps to reproduce (markdown supported)"
    )

    issue_type: Mapped[IssueType] = mapped_column(
        nullable=False,
        default=IssueType.TASK,
        comment="Issue type determining workflow and available fields"
    )

    status: Mapped[IssueStatus] = mapped_column(
        nullable=False,
        default=IssueStatus.BACKLOG,
        comment="Current workflow state in Kanban board"
    )

    priority: Mapped[Priority] = mapped_column(
        nullable=False,
        default=Priority.MEDIUM,
        comment="Business priority for work ordering"
    )

    # Foreign keys for assignments and relationships
    # Why separate assignee/assignee_id vs. always loading:
    # - Optional assignment (some issues unassigned)
    # - Lazy loading for performance (don't fetch user data unnecessarily)
    # - Tradeoff: Additional queries vs. memory usage/eagerness
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id"),
        nullable=False,
        comment="Parent project containing this issue"
    )

    reporter_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        comment="User who created/reported this issue"
    )

    assignee_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        comment="Optional user currently assigned to work on this issue"
    )

    # Relationships with back-references
    # Why explicit back_populates: Clear bidirectional navigation
    # Alternative: implicit backrefs (magical, hard to maintain)
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="issues"
    )

    reporter: Mapped["User"] = relationship(
        "User",
        back_populates="reported_issues",
        foreign_keys=[reporter_id]
    )

    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_issues",
        foreign_keys=[assignee_id]
    )

    # Business logic properties
    @property
    def key(self) -> str:
        """Generate Jira-style issue key (e.g., PROJ-123).

        Why lazy property: Computed field that depends on relationships.
        Issues current implementation limitations due to async considerations.

        Educational Note: Properties encapsulate business logic in models.
        - Benefits: DRY, centralizes issue key logic
        - Alternative: Helper function (scattered logic)
        - Alternative: Database-computed field (vendor-specific)
        """
        if hasattr(self, 'project') and self.project:
            return self.project.generate_issue_key(self.issue_number)
        return f"UNKNOWN-{self.issue_number}"

    @property
    def is_resolved(self) -> bool:
        """Check if issue is in a resolved state.

        Educational Note: Business logic in models for performance.
        - Properties: Fast, cached by instance
        - Functions: Repeated computation on each call
        """
        return self.status == IssueStatus.DONE

    def can_be_assigned_to(self, user_id: str) -> bool:
        """Check if a user can be assigned to this issue.

        Why model method: Business rules centralization.
        Currently simplistic - future access control logic here.
        """
        # For now: any active user in the project can be assigned
        # Future: Implement role-based assignment restrictions
        return True

    def transition_status(self, new_status: IssueStatus) -> bool:
        """Attempt to transition issue to new status.

        Why model method: Encapsulate business rules and validation.
        Returns boolean for success/failure indication.

        Educational Note: State machine pattern in models.
        - Benefits: Centralized transition logic
        - Current: Simple validation (future: complex workflow)
        """
        # Basic validation - prevent invalid transitions
        current_idx = list(IssueStatus).index(self.status)
        new_idx = list(IssueStatus).index(new_status)

        # Prevent reverse transitions (backlog -> to_do, but not back)
        # Exception: Allow any transition to DONE (closing issues)
        if new_status != IssueStatus.DONE and new_idx < current_idx:
            return False

        self.status = new_status
        return True

    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.key}: {self.title}"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"<Issue(id={self.id}, key={self.key}, status={self.status}, type={self.issue_type})>"