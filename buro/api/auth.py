# buro/api/auth.py
#
# Authentication router for user login and JWT token management.
#
# Educational Notes for Junior Developers:
# - JWT vs. Sessions: Stateless authentication, scalable across multiple servers.
#   Tradeoff: No server-side invalidation vs. smaller payload/requests.
# - HTTP-only cookies: Prevent XSS attacks by making tokens inaccessible to JavaScript.
#   Tradeoff: More complex frontend handling vs. security.
# - Refresh tokens: Provide long-term authentication without exposing access tokens.
#   Tradeoff: Additional complexity vs. better security.

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from buro.core.database import get_db
from buro.models import User

# Why HTTPBearer: Secure way to transmit JWT in Authorization header
# Alternative: OAuth2PasswordBearer (more complex configuration)
security = HTTPBearer()

# Authentication configuration
# Why environment variables: Don't hardcode secrets in source code
SECRET_KEY = "your-secret-key-here"  # In production: os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Pydantic schemas for request/response validation
# Why Pydantic: Type validation, automatic documentation, serialization
class LoginRequest(BaseModel):
    """Schema for user login requests.

    Why email only: Simplified UX, email-based authentication common in modern apps.
    Tradeoff: No username support vs. familiar login pattern.
    """
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """JWT token response schema.

    Why access_token only: Simplified for this MVP.
    Future: Add refresh_token for better security.
    """
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    """Public user information for API responses.

    Why separate from User model: Won't leak password hashes or sensitive data.
    Principle: API responses should be intentional, not direct model dumps.
    """
    id: str
    email: str
    full_name: str
    role: str
    avatar_url: Optional[str] = None

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        """Factory method to create response from User model.

        Why classmethod: Alternative constructor pattern.
        Benefits: Clear conversion logic, testable independently.
        """
        return cls(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            avatar_url=user.avatar_url
        )

# Dependency function: Extract user from JWT token
# Why dependency injection: Clean separation of concerns, testable auth logic
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extract and validate current user from JWT token.

    Why Depends(security): Automatic token extraction from Authorization header.
    Why async: Database lookup for user information.

    Educational Note: This pattern is used by all protected endpoints.
    Raises HTTPException automatically when auth fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token payload
        # Why no verification in development: Simpler debugging
        # Production: Should use SECRET_KEY for signature verification
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Fetch user from database
    # Why by ID only: Sub claim should be user ID (authoritative)
    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exception

    return user

# Optional user dependency - for endpoints that work with/without auth
# Why Optional[User]: Allows conditional logic in routes
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise.

    Why separate function: Avoid try/catch in every route.
    Useful for public endpoints that show different data to logged-in users.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

# Utility functions for JWT token handling
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token with expiration.

    Why expiration: Security best practice, prevents indefinite access.
    Why issuer/subject claims: Standard JWT fields for identification.

    Educational Note: JWT payload should be minimal - only necessary data.
    Never include sensitive information - it's easily decoded.
    """
    to_encode = data.copy()

    # Set token expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})

    # Create and sign the token
    # Why HS256: Symmetric encryption, simpler key management
    # Tradeoff: Same key for signing/verification vs. RSA complexity
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# API Router definition
router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Authenticate user and return JWT access token.

    Why POST: Login involves sending credentials (not GET for security).
    Why async: Potential for rate limiting or external auth checks later.

    Educational Note: This is the entry point to the application.
    Consider implementing rate limiting to prevent brute force attacks.
    """
    # Find user by email
    # Why case-insensitive: Email addresses are case-insensitive by standard
    user_stmt = select(User).where(func.lower(User.email) == request.email.lower())
    result = await db.execute(user_stmt)
    user = result.scalar_one_or_none()

    # Validate credentials
    if not user or not user.verify_password(request.password):
        # Why generic message: Don't leak information about valid emails
        # Helps prevent user enumeration attacks
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Generate access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},  # Subject claim (user ID)
        expires_delta=access_token_expires
    )

    return TokenResponse(access_token=access_token)

@router.post("/register", response_model=TokenResponse)
async def register(
    request: LoginRequest,
    full_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user account.

    Why POST /register: Separate from login for security and workflow.
    Allows user onboarding, email verification, etc.

    Educational Note: Registration vs Login separation allows:
    - Different validation rules
    - Email verification workflows
    - Administrative approval processes
    """
    # Import services here to avoid circular imports
    from buro.services.auth_service import AuthService
    from buro.services.user_service import UserService

    user_service = UserService(db)
    auth_service = AuthService(db, user_service)

    # Create new user
    user = await auth_service.register_user(
        email=request.email,
        full_name=full_name,
        password=request.password
    )

    # Generate access token for immediate login
    return await auth_service.create_user_token(user)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current authenticated user's information.

    Why GET /me: Standard pattern for user profile endpoints.
    Useful for displaying user info in app header/sidebar.

    Educational Note: Protected route - requires valid JWT token.
    The dependency automatically validates and provides the user.
    """
    return UserResponse.from_user(current_user)

@router.post("/logout")
async def logout() -> dict:
    """Logout endpoint (conceptual implementation).

    Why simple response: Stateless JWT means no server-side logout needed.
    Client should discard the token.

    Educational Note: In production, consider token blacklisting for
    scenarios where immediate logout is required (password change, etc.)
    """
    return {"message": "Successfully logged out"}

# Import required for the db query in login function
from sqlalchemy import select, func