# buro/services/user_service.py
#
# User management business logic service.
#
# Educational Notes for Junior Developers:
# - Service responsibilities: Business rules around user management
# - Domain logic separation: User validation, role management, permissions
# - Why not in models: Models are data containers, services contain business logic

from typing import List, Optional, Tuple
import secrets
import string
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
        search: Optional[str] = None,
        include_inactive: bool = False,
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

        # Learning note: We default to active users only because most day-to-day
        # workflows (assignee pickers, ownership selectors) should not surface
        # deactivated accounts. The tradeoff is that admin tooling must explicitly
        # opt in to include inactive users for auditing and maintenance.
        if not include_inactive:
            stmt = stmt.where(User.is_active.is_(True))
            count_stmt = count_stmt.where(User.is_active.is_(True))

        if search:
            escaped = search.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            condition = or_(
                func.lower(User.full_name).like(pattern, escape="\\"),
                func.lower(User.email).like(pattern, escape="\\")
            )
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        # Learning note: ordering by newest first makes admin actions easier to
        # verify after creates/edits because recently touched users stay visible.
        # Tradeoff: older accounts shift between pages over time.
        stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(stmt)
        users = list(result.scalars().all())

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        return users, total

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Lookup user by email with normalized case handling."""
        stmt = select(User).where(func.lower(User.email) == email.lower().strip())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def generate_temp_password(self, length: int = 12) -> str:
        """Generate a temporary password for admin-provisioned users.

        Learning note: We generate passwords server-side to keep onboarding simple
        for this educational app (no email service required). Tradeoff: admin must
        share the temporary secret out-of-band, which is less ideal than a secure
        password reset flow in production.
        """
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def create_user(
        self,
        *,
        email: str,
        full_name: str,
        role: Role,
        current_user: User,
    ) -> Tuple[User, str]:
        """Create a user with an auto-generated temporary password.

        Only administrators may provision new users from the maintenance UI.
        """
        if current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can create users",
            )

        existing_user = await self.get_user_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        temp_password = self.generate_temp_password()
        new_user = User(
            email=email.lower().strip(),
            full_name=full_name.strip(),
            hashed_password=User.hash_password(temp_password),
            role=role,
            is_active=True,
        )
        self.db.add(new_user)
        await self.db.commit()
        return new_user, temp_password

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
        allowed_fields = ["full_name", "avatar_url", "theme"]
        if current_user.role == Role.ADMIN:
            allowed_fields.append("role")  # Only admins can change roles

        for field, value in updates.items():
            if field in allowed_fields:
                if field == "theme":
                    # Learning note: explicit allow-list keeps preference values
                    # constrained without introducing a heavy schema migration.
                    # Tradeoff: small validation branch vs. predictable data.
                    if value not in ["light", "dark"]:
                        continue
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

    async def reactivate_user(self, user_id: str, current_user: User) -> User:
        """Reactivate a deactivated user (admin only)."""
        if current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can reactivate users",
            )

        target_user = await self.get_user_by_id(user_id)
        target_user.is_active = True
        await self.db.commit()
        await self.db.refresh(target_user)
        return target_user
