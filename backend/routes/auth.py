"""
Authentication Routes

JWT-based session authentication endpoints.
Part of PRD-036: Session Authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from datetime import datetime

from backend.utils.auth import (
    AUTH_USERNAME,
    AUTH_PASSWORD,
    create_access_token,
    decode_token,
    should_refresh_token,
    verify_jwt_or_basic,
)
from backend.utils.rate_limiter import limiter, RATE_LIMITS
import secrets

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class LoginRequest(BaseModel):
    """Login request with username and password."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response with JWT token."""
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    username: str


class TokenRefreshResponse(BaseModel):
    """Token refresh response with new JWT."""
    access_token: str
    expires_at: str
    username: str


class UserInfoResponse(BaseModel):
    """Current user information response."""
    username: str
    expires_at: str
    should_refresh: bool


class LogoutResponse(BaseModel):
    """Logout confirmation response."""
    message: str
    success: bool


# ============================================================================
# Auth Endpoints
# ============================================================================

@router.post("/login", response_model=LoginResponse)
@limiter.limit(RATE_LIMITS["default"])
async def login(request: Request, login_data: LoginRequest):
    """
    Authenticate with username and password, receive JWT token.

    Returns JWT access token valid for 24 hours.
    """
    # Development mode: allow any credentials if no password configured
    if not AUTH_PASSWORD:
        token, expires_at = create_access_token(login_data.username)
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at.isoformat(),
            username=login_data.username
        )

    # Verify credentials using timing-attack-resistant comparison
    username_correct = secrets.compare_digest(
        login_data.username.encode("utf8"),
        AUTH_USERNAME.encode("utf8")
    )
    password_correct = secrets.compare_digest(
        login_data.password.encode("utf8"),
        AUTH_PASSWORD.encode("utf8")
    )

    if not (username_correct and password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Create JWT token
    token, expires_at = create_access_token(login_data.username)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_at=expires_at.isoformat(),
        username=login_data.username
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(user: str = Depends(verify_jwt_or_basic)):
    """
    Log out the current user.

    Since we're using stateless JWT tokens without a blacklist,
    logout is handled client-side by discarding the token.
    This endpoint confirms successful logout.
    """
    return LogoutResponse(
        message="Successfully logged out",
        success=True
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
@limiter.limit(RATE_LIMITS["default"])
async def refresh_token(request: Request, user: str = Depends(verify_jwt_or_basic)):
    """
    Refresh the current JWT token.

    Returns a new token with extended expiration.
    Use this before the current token expires.
    """
    # Create new token for the authenticated user
    token, expires_at = create_access_token(user)

    return TokenRefreshResponse(
        access_token=token,
        expires_at=expires_at.isoformat(),
        username=user
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user(
    request: Request,
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Get information about the current authenticated user.

    Returns username and token status.
    """
    # Try to get token from Authorization header to check expiration
    auth_header = request.headers.get("Authorization", "")
    should_refresh = False

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        should_refresh = should_refresh_token(token)
        # Get expiration from token
        try:
            payload = decode_token(token)
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                expires_at = datetime.utcfromtimestamp(exp_timestamp).isoformat() + "Z"
            else:
                expires_at = "unknown"
        except Exception:
            expires_at = "unknown"
    else:
        # Basic Auth - no expiration concept
        expires_at = "N/A (Basic Auth)"

    return UserInfoResponse(
        username=user,
        expires_at=expires_at,
        should_refresh=should_refresh
    )
