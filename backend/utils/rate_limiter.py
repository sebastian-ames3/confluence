"""
Rate Limiting Utilities

API rate limiting using slowapi to prevent abuse and protect Claude API budget.
Part of PRD-015: Security Hardening.
"""

import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

# Get rate limit configurations from environment or use defaults
DEFAULT_RATE_LIMIT = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")
SYNTHESIS_RATE_LIMIT = os.getenv("RATE_LIMIT_SYNTHESIS", "10/hour")
TRIGGER_RATE_LIMIT = os.getenv("RATE_LIMIT_TRIGGER", "5/hour")
SEARCH_RATE_LIMIT = os.getenv("RATE_LIMIT_SEARCH", "60/minute")


def get_client_ip(request: Request) -> str:
    """
    Get client IP address, handling proxies.

    Checks X-Forwarded-For header first (for Railway/proxy deployments),
    then falls back to direct client address.
    """
    # Check for forwarded header (Railway, nginx, etc.)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs; take the first (original client)
        return forwarded.split(",")[0].strip()

    # Fall back to direct connection
    return get_remote_address(request)


# Rate limiter instance with custom key function
limiter = Limiter(key_func=get_client_ip)


# Rate limit configurations for different endpoint types
RATE_LIMITS = {
    "default": DEFAULT_RATE_LIMIT,
    "synthesis": SYNTHESIS_RATE_LIMIT,  # Expensive Claude calls
    "trigger": TRIGGER_RATE_LIMIT,       # Collection triggers
    "search": SEARCH_RATE_LIMIT,         # Database queries
}


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.

    Returns JSON response with rate limit information.
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
            "retry_after": exc.detail.split("per")[0].strip() if exc.detail else "unknown"
        },
        headers={
            "Retry-After": "60",  # Suggest retry after 60 seconds
            "X-RateLimit-Limit": str(exc.detail) if exc.detail else "unknown"
        }
    )
