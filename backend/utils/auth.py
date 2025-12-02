"""
Authentication Utilities

HTTP Basic Auth implementation for protecting API endpoints.
Part of PRD-015: Security Hardening.
"""

import os
import secrets
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# HTTP Basic Auth security scheme
security = HTTPBasic(auto_error=False)

# Credentials from environment
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD")  # Required in production


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
