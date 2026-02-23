# buro/models/__init__.py
#
# Models package for SQLAlchemy table definitions and relationships.
#
# Educational Notes for Junior Developers:
# - Package-level imports: Makes models discoverable for imports like
#   'from buro.models import User, Project, Issue'
# - Following Domain-Driven Design: Related entities grouped together
# - Why import all models: Simplifies database initialization and migrations
#   Tradeoff: Imports all models on any import vs. convenient access

# Import all models to make them available for database operations
# This ensures SQLAlchemy can discover all relationships during schema creation
from .base import Base
from .user import User, Role
from .project import Project
from .issue import Issue, IssueType, IssueStatus, Priority

# For convenience, expose commonly used enums at package level
# Tradeoff: Pollutes namespace vs. developer convenience
__all__ = [
    "Base",
    "User", "Role",
    "Project",
    "Issue", "IssueType", "IssueStatus", "Priority"
]