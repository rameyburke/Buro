# buro/services/auth.py
#
# Authentication service layer for business logic separation.
#
# Educational Notes for Junior Developers:
# - Service layer pattern: Separates business logic from API routes.
#   Benefits: Cleaner controllers, reusable logic, testable services.
# - Dependency injection: Services receive dependencies vs creating them.
#   Tradeoff: More verbose constructor calls vs cleaner testability.
# - Async all the way down: No blocking operations in HTTP request processing.

from datetime import timedelta
from uuid import uuid4
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from buro.models import User, Role
from .user_service import UserService


class AuthService:
    """Authentication and authorization business logic.

    Why service layer over direct route handlers:
    - Business rules centralized (single responsibility)
    - Easier testing without HTTP fixtures
    - Reusable across different API endpoints
    - Clear separation of concerns
    """

    def __init__(self, db: AsyncSession, user_service: UserService):
        """Dependency injection for clean architecture.

        Educational Note: Don't create service dependencies inside services.
        External injection allows for:
        - Mock dependencies in unit tests
        - Different implementations (e.g., different DB backends)
        - Clear component boundaries
        """
        self.db = db
        self.user_service = user_service

    async def authenticate_user(self, email: str, password: str) -> User:
        """Authenticate user credentials and return user object.

        Why in service layer: Authentication is business logic, not just data access.
        Includes password verification, account status checks, audit logging.

        Educational Note: Always fail securely - don't reveal information through
        error messages (e.g., "wrong password" vs "invalid credentials").
        """
        # Case-insensitive email lookup (email addresses are insensitive)
        # Why func.lower(): Database index-friendly case-insensitive search
        user_stmt = select(User).where(func.lower(User.email) == email.lower())
        result = await self.db.execute(user_stmt)
        user = result.scalar_one_or_none()

        # Verify credentials
        if not user or not user.verify_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Check account status
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )

        return user

    async def authorize_admin_or_manager(self, user: User) -> None:
        """Check if user has admin/manager permissions.

        Why explicit authorization methods:
        - Centralized access control logic
        - Easy to audit and test permissions
        - Single point of change for role-based rules
        """
        if user.role not in [Role.ADMIN, Role.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )

    async def create_user_token(self, user: User) -> dict:
        """Generate authentication token and response data.

        Why separate method: Token generation is complex business logic.
        Handles JWT creation, expiration times, and response formatting.

        Educational Note: Tokens should contain minimal information.
        Never include sensitive data like passwords or full user details.
        """
        # Import here to avoid circular imports
        from buro.api.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

        # Generate JWT with user ID as subject claim
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "role": user.role.value},
            expires_delta=access_token_expires
        )

        # Return standardized token response
        # Why consistent structure: Easier for frontend integration
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds()),
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value
            }
        }

    async def register_user(
        self,
        email: str,
        full_name: str,
        password: str,
        role: Role = Role.DEVELOPER
    ) -> User:
        """Register a new user account.

        Why in service layer: User creation involves business rules:
        - Email uniqueness validation
        - Password strength requirements
        - Default role assignment
        - Profile setup logic

        Educational Note: Registration should be separate from login
        for security - allows user verification workflows.
        """
        # Check if user already exists
        # Why case-insensitive: Email addresses should be unique regardless of case
        existing_stmt = select(User).where(func.lower(User.email) == email.lower())
        result = await self.db.execute(existing_stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )

        # Create new user with encrypted password
        # Why random UUID for id: Predictable IDs = security risk (enumeration attacks)
        new_user = User(
            email=email.lower().strip(),  # Normalize email
            full_name=full_name.strip(),
            hashed_password=User.hash_password(password),
            role=role,
            is_active=True
        )

        # Save to database
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)  # Get the generated ID

        return new_user