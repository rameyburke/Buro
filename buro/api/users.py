# buro/api/users.py
#
# Users API router for user management operations.
#
# Educational Notes for Junior Developers:
# - User management: List, update profiles with proper permissions.
# - Role-based access: Admins/managers have more permissions than developers.

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from buro.core.database import get_db
from buro.models import User
from buro.api.auth import get_current_user

class UserResponse(BaseModel):
    """Public user information schema."""
    id: str
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None
    is_active: bool

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            avatar_url=user.avatar_url,
            is_active=user.is_active
        )

class UserListResponse(BaseModel):
    """Paginated user list response."""
    users: List[UserResponse]
    total: int
    skip: int
    limit: int

router = APIRouter()

@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None, description="Search by name or email"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users (admin/manager only).

    Why protected: User enumeration could be privacy/security concern.
    Only privileged roles should see full user list.
    """
    # Import service here to avoid circular imports
    from buro.services.user_service import UserService

    user_service = UserService(db)

    try:
        users, total = await user_service.get_users(
            current_user=current_user,
            skip=skip,
            limit=limit,
            search=search
        )

        return UserListResponse(
            users=[UserResponse.from_user(user) for user in users],
            total=total,
            skip=skip,
            limit=limit
        )
    except HTTPException:
        raise

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user's own profile information."""
    return UserResponse.from_user(current_user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    updates: dict,  # Would use proper schema in production
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user profile with permissions.

    Why flexible updates: Different fields have different permission rules.
    Pure route - business logic in service layer.
    """
    from buro.services.user_service import UserService

    user_service = UserService(db)

    try:
        updated_user = await user_service.update_user_profile(
            user_id=user_id,
            current_user=current_user,
            updates=updates
        )

        return UserResponse.from_user(updated_user)
    except HTTPException:
        raise
