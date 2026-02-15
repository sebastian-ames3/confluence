"""
Authentication Utilities

HTTP Basic Auth and JWT implementation for protecting API endpoints.
Part of PRD-015: Security Hardening.
Part of PRD-036: Session Authentication (JWT).
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

# HTTP Basic Auth security scheme
security = HTTPBasic(auto_error=False)

# HTTP Bearer (JWT) security scheme (PRD-036)
bearer_scheme = HTTPBearer(auto_error=False)

# Credentials from environment
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD")  # Required in production

# JWT Configuration (PRD-036)
_jwt_secret_env = os.getenv("JWT_SECRET")
JWT_SECRET = _jwt_secret_env or AUTH_PASSWORD or "dev-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
JWT_REFRESH_THRESHOLD_MINUTES = 60  # Refresh if expires within 60 minutes

# Fail hard in production if critical auth vars are missing
import logging as _auth_logging
_is_production = os.getenv("RAILWAY_ENV") == "production"
if _is_production and not AUTH_PASSWORD:
    raise RuntimeError("AUTH_PASSWORD must be set in production")
if _is_production and not _jwt_secret_env and AUTH_PASSWORD:
    _auth_logging.getLogger(__name__).warning(
        "JWT_SECRET not set - falling back to AUTH_PASSWORD. Set a separate JWT_SECRET for better security."
    )


def verify_credentials(
    credentials: Optional[HTTPBasicCredentials] = Security(security)
) -> str:
    """
    Verify HTTP Basic Auth credentials.

    In production (AUTH_PASSWORD set), requires valid credentials.
    In development (AUTH_PASSWORD not set), allows anonymous access with warning.

    Args:
        credentials: HTTP Basic Auth credentials from request

    Returns:
        Username if authenticated, "anonymous" if dev mode

    Raises:
        HTTPException: 401 if credentials invalid, 500 if misconfigured
    """
    # Development mode: allow unauthenticated access if no password configured
    if not AUTH_PASSWORD:
        # Log warning but allow access for local development
        import logging
        logging.warning(
            "AUTH_PASSWORD not configured - allowing unauthenticated access. "
            "Set AUTH_PASSWORD environment variable for production!"
        )
        return "anonymous"

    # Production mode: require valid credentials
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Use secrets.compare_digest to prevent timing attacks
    username_correct = secrets.compare_digest(
        credentials.username.encode("utf8"),
        AUTH_USERNAME.encode("utf8")
    )
    password_correct = secrets.compare_digest(
        credentials.password.encode("utf8"),
        AUTH_PASSWORD.encode("utf8")
    )

    if not (username_correct and password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


def get_optional_user(
    credentials: Optional[HTTPBasicCredentials] = Security(security)
) -> Optional[str]:
    """
    Get user if authenticated, None otherwise.

    Use this for endpoints that work differently for authenticated vs anonymous users.

    Args:
        credentials: HTTP Basic Auth credentials from request

    Returns:
        Username if authenticated, None otherwise
    """
    if not credentials or not AUTH_PASSWORD:
        return None

    try:
        return verify_credentials(credentials)
    except HTTPException:
        return None


# ============================================================================
# PRD-036: JWT Session Authentication
# ============================================================================

def create_access_token(username: str) -> tuple[str, datetime]:
    """
    Create a JWT access token for the given username.

    Args:
        username: The username to encode in the token

    Returns:
        Tuple of (token_string, expiration_datetime)
    """
    expires_at = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": username,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires_at


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token string

    Returns:
        The decoded payload dict

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_token_expiration(token: str) -> Optional[datetime]:
    """
    Get the expiration time of a token without full validation.

    Args:
        token: The JWT token string

    Returns:
        Expiration datetime or None if invalid
    """
    try:
        # Decode without verification to get expiration
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
        return None
    except Exception:
        return None


def should_refresh_token(token: str) -> bool:
    """
    Check if a token should be refreshed (expires within threshold).

    Args:
        token: The JWT token string

    Returns:
        True if token expires within JWT_REFRESH_THRESHOLD_MINUTES
    """
    exp = get_token_expiration(token)
    if not exp:
        return True  # Invalid token, should refresh

    threshold = datetime.now(timezone.utc) + timedelta(minutes=JWT_REFRESH_THRESHOLD_MINUTES)
    return exp <= threshold


def verify_jwt_or_basic(
    credentials: Optional[HTTPBasicCredentials] = Security(security),
    bearer_token: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> str:
    """
    Verify authentication via JWT Bearer token OR HTTP Basic Auth.

    Provides backward compatibility - local scripts can use Basic Auth
    while the frontend uses JWT tokens.

    Priority: Bearer token > Basic Auth

    Args:
        credentials: HTTP Basic Auth credentials from request
        bearer_token: Bearer token from Authorization header

    Returns:
        Username if authenticated

    Raises:
        HTTPException: 401 if neither auth method succeeds
    """
    # Try Bearer token first (JWT)
    if bearer_token and bearer_token.credentials:
        try:
            payload = decode_token(bearer_token.credentials)
            username = payload.get("sub")
            if username:
                return username
        except HTTPException:
            # Token invalid, fall through to try Basic Auth
            pass

    # Fall back to Basic Auth
    if credentials:
        try:
            return verify_credentials(credentials)
        except HTTPException:
            pass

    # Development mode: allow unauthenticated access if no password configured
    if not AUTH_PASSWORD:
        import logging
        logging.warning(
            "AUTH_PASSWORD not configured - allowing unauthenticated access. "
            "Set AUTH_PASSWORD environment variable for production!"
        )
        return "anonymous"

    # Neither method succeeded
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
