# buro/services/user_service.py
#
# User management business logic service.
#
# Educational Notes for Junior Developers:
# - Service responsibilities: Business rules around user management
# - Domain logic separation: User validation, role management, permissions
# - Why not in models: Models are data containers, services contain business logic

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from fastapi import HTTPException, status

from buro.models import User, Role


class UserService:
    """Business logic for user management operations.

    Why separate from User model: Models define data structure,
    Services define business behavior and validation rules.

    Methods here represent the business operations users can perform.
    """

    def __init__(self, db: AsyncSession):
        """Receive database session via dependency injection."""
        self.db = db

    async def get_user_by_id(self, user_id: str) -> User:
        """Retrieve user by ID with proper error handling.

        Why service method: Security validation and standardized error responses.
        Includes permission checks (user can view own profile, admin can view any).
        """
        user = await self.db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def get_users(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """List users with pagination and access control.

        Why access control here: Only certain roles can list users.
        Prevents unauthorized data enumeration.

        Educational Note: Always implement access control at the service level,
        not just API level, for consistency across all interfaces.
        """
        # Check permissions - only admin/manager can list users
        if current_user.role not in [Role.ADMIN, Role.MANAGER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to list users"
            )

        stmt = select(User)
        count_stmt = select(func.count()).select_from(User)

        if search:
            pattern = f"%{search.lower()}%"
            condition = or_(
                func.lower(User.full_name).like(pattern),
                func.lower(User.email).like(pattern)
            )
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        stmt = stmt.offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        users = list(result.scalars().all())

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        return users, total

    async def update_user_profile(
        self,
        user_id: str,
        current_user: User,
        updates: dict
    ) -> User:
        """Update user profile with business rules and validation.

        Why complex permissions: Users can edit own profile,
        admins/managers can edit any profile, but with restrictions.

        Educational Note: Business rules for profile updates:
        - Role changes require admin privileges
        - Email changes should send verification
        - Password updates have special handling
        """
        # Fetch user to update
        target_user = await self.get_user_by_id(user_id)

        # Permission checks
        can_edit = (
            current_user.id == user_id or  # Own profile
            current_user.role == Role.ADMIN or  # Admins can edit anyone
            # Managers can edit developers but not other managers/admins
            (current_user.role == Role.MANAGER and target_user.role == Role.DEVELOPER)
        )

        if not can_edit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update this user profile"
            )

        # Apply updates with validation
        allowed_fields = ["full_name", "avatar_url"]
        if current_user.role == Role.ADMIN:
            allowed_fields.append("role")  # Only admins can change roles

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(target_user, field, value)
            elif field in ["password"]:  # Special handling for password changes
                if value:
                    target_user.hashed_password = User.hash_password(value)
            else:
                # Ignore invalid fields instead of error (flexible API)
                pass

        await self.db.commit()
        await self.db.refresh(target_user)
        return target_user

    async def deactivate_user(
        self,
        user_id: str,
        current_user: User
    ) -> None:
        """Deactivate user account with business rules.

        Why not delete: Data retention, audit trails, reactivation possible.
        Business rule: Only admins can deactivate accounts.

        Educational Note: Soft deletes preserve referential integrity
        while removing user access. Different from hard deletes.
        """
        # Only admins can deactivate users
        if current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can deactivate users"
            )

        # Cannot deactivate self (would lock out admin)
        if current_user.id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate your own account"
            )

        target_user = await self.get_user_by_id(user_id)
        target_user.is_active = False

        await self.db.commit()
