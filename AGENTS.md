# Agent Guidelines for Buro Repository

This document provides guidelines and commands for agentic coding assistants working with this Python codebase.

## Environment Setup

### Python Version
- Use Python 3.8+ (check pyproject.toml for exact version requirements)
- Consider using uv, poetry, or pip for dependency management

### Virtual Environment
```bash
# Using uv (preferred if uv.lock exists)
uv venv
source .venv/bin/activate  # Linux/Mac
# or .venv/Scripts/activate  # Windows

# Using venv directly
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
```

### Installing Dependencies
```bash
# Using uv
uv sync

# Using poetry
poetry install

# Using pip
pip install -e .
```

## Development Commands

### Running the Application
```bash
# Add application run commands here when available
# Examples:
# python -m buro.main
# flask run
# uvicorn buro.app:app --reload
```

### Testing

#### Run All Tests
```bash
# Using pytest (recommended)
pytest

# Using unittest
python -m unittest discover

# Using tox (for multiple environments)
tox
```

#### Run Single Test
```bash
# Single test file
pytest tests/test_specific_file.py

# Single test function
pytest tests/test_file.py::TestClass::test_method

# Single test with verbose output
pytest -v tests/test_file.py::TestClass::test_method

# Run tests matching pattern
pytest -k "test_name"
```

#### Test Coverage
```bash
# Generate coverage report
pytest --cov=buro --cov-report=html
pytest --cov=buro --cov-report=term-missing

# Open HTML coverage report
open htmlcov/index.html  # Mac
start htmlcov/index.html  # Windows
```

### Linting & Code Quality

#### Ruff (Primary Linter - Fast Python Linting)
```bash
# Check all files
ruff check .

# Fix auto-fixable issues
ruff check . --fix

# Check specific file
ruff check path/to/file.py

# Check with preview features
ruff check . --preview
```

#### MyPy (Type Checking)
```bash
# Type check all files
mypy .

# Type check single file
mypy path/to/file.py

# Strict type checking
mypy . --strict
```

#### Black (Code Formatting)
```bash
# Format all files
black .

# Check format without changes
black --check .
```

### Code Quality Checks
```bash
# Run all quality checks
ruff check . && mypy . && black --check .

# Format and fix issues
black . && ruff check . --fix
```

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

## Code Style Guidelines

### Python Standards

#### PEP 8 Compliance
- Use Black for consistent formatting (88 char line length)
- Follow standard Python naming conventions
- Maximum line length: 88 characters (Black default)

#### Import Style
```python
# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import requests
from pydantic import BaseModel

# Local imports (use relative imports within package)
from . import utils
from ..config import settings
```

**Import Order Rules:**
1. Standard library imports
2. Third-party imports (alphabetical)
3. Local imports (alphabetical)
4. One blank line between each import group

#### Type Hints
```python
from typing import Dict, List, Optional, Union

def process_data(data: Dict[str, Union[int, str]], count: int = 0) -> Optional[List[str]]:
    """Process data and return result."""
    pass

# Use generics for type safety
from typing import TypeVar, Generic
T = TypeVar('T')

class Repository(Generic[T]):
    def get_by_id(self, id: int) -> Optional[T]:
        pass
```

#### Docstrings
Use Google-style docstrings:
```python
def calculate_total(items: List[Dict[str, float]], tax_rate: float = 0.0) -> float:
    """Calculate total cost including tax.

    Args:
        items: List of items with 'price' and 'quantity' keys.
        tax_rate: Tax rate as decimal (e.g., 0.08 for 8%).

    Returns:
        Total cost including tax.

    Raises:
        ValueError: If items contain invalid data.

    Example:
        >>> calculate_total([{'price': 10.0, 'quantity': 2}], 0.1)
        22.0
    """
    pass
```

### Naming Conventions

#### Variables and Functions
- Use `snake_case` for variables, functions, and methods
- Use `UPPER_CASE` for constants
```python
user_name = "john"
DEFAULT_TIMEOUT = 30

def calculate_total():
    pass
```

#### Classes and Types
- Use `PascalCase` for classes and types
```python
class UserService:
    pass

from typing import TypeAlias
UserID = str
```

#### Modules and Packages
- Use `snake_case` for module names
- Keep package names short and descriptive
```python
# mypackage/
#   user_service.py
#   data_models.py
```

### Error Handling

#### Exception Best Practices
```python
# Good: Specific exception handling
def read_file(filename: str) -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {filename}")
    except PermissionError:
        raise PermissionError("Permission denied reading configuration file")

# Avoid bare except clauses
try:
    risky_operation()
except Exception as e:  # Too broad
    logger.error(f"Unexpected error: {e}")

# Prefer specific exception types
try:
    risky_operation()
except (ValueError, TypeError) as e:
    logger.error(f"Invalid input: {e}")
except ConnectionError as e:
    logger.error(f"Network error: {e}")
```

#### Custom Exceptions
```python
class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass
```

### Logging

#### Logger Setup
```python
import logging

# Module-level logger
logger = logging.getLogger(__name__)

def setup_logging(level: str = "INFO") -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log")
        ]
    )
```

#### Logging Levels
```python
# Use appropriate log levels
logger.debug("Detailed information for debugging")
logger.info("General information about application progress")
logger.warning("Something unexpected but not critical")
logger.error("An error occurred that should be investigated")
logger.critical("A serious error that may cause the application to stop")
```

### Testing

#### Test Structure
```python
import pytest
from unittest.mock import Mock, patch

class TestUserService:
    def test_successful_registration(self):
        """Test successful user registration."""
        service = UserService()

        # Given
        user_data = {"email": "test@example.com", "name": "Test User"}

        # When
        result = service.register_user(user_data)

        # Then
        assert result.success is True
        assert result.user_id is not None

    @patch('services.email_service.EmailService.send_welcome')
    def test_registration_sends_email(self, mock_send_email):
        """Test that registration sends welcome email."""
        service = UserService()

        service.register_user({"email": "test@example.com"})

        mock_send_email.assert_called_once_with("test@example.com")
```

#### Test Naming
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Security Best Practices

#### Input Validation
```python
from pydantic import BaseModel, validator
from typing import Optional

class CreateUserRequest(BaseModel):
    email: str
    name: str
    age: Optional[int] = None

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v

    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v
```

#### Secure Coding
- Never store secrets in code (use environment variables)
- Use parameterized queries for SQL
- Validate and sanitize all inputs
- Use HTTPS URLs
- Keep dependencies updated for security patches

### Configuration

#### Environment Variables
```python
from os import getenv
from typing import Optional

class Settings:
    database_url: str = getenv("DATABASE_URL", "sqlite:///app.db")
    secret_key: str = getenv("SECRET_KEY", "")
    debug: bool = getenv("DEBUG", "false").lower() == "true"

    def __post_init__(self):
        if not self.secret_key:
            raise ValueError("SECRET_KEY environment variable is required")
```

### Cursor Rules

*No Cursor rules found in .cursor/rules/ or .cursorrules. Add rules here if available.*

### Copilot Rules

*No Copilot rules found in .github/copilot-instructions.md. Add rules here if available.*

---

**Last Updated:** February 2026
**Maintainer:** Development Team</content>
<parameter name="filePath">/mnt/c/Users/ramey/source/repos/Buro/AGENTS.md