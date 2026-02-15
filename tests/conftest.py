"""
Pytest configuration and fixtures.
"""
import os
import pytest
import pytest_asyncio
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure test environment variables are set before any imports
os.environ.setdefault("RAILWAY_ENV", "testing")
os.environ.setdefault("AUTH_USERNAME", "testuser")
os.environ.setdefault("AUTH_PASSWORD", "testpassword")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("CLAUDE_API_KEY", "test-dummy-key")


# --- Legacy fixtures (kept for existing tests) ---

@pytest.fixture(scope="session")
def test_db():
    """Provide a test database instance (legacy)."""
    from backend.utils.db import get_db
    return get_db()


@pytest.fixture(scope="session")
def usage_limiter():
    """Provide a usage limiter instance."""
    from backend.utils.usage_limiter import get_usage_limiter
    return get_usage_limiter()


# --- New behavioral test fixtures ---

@pytest.fixture(scope="session")
def test_app():
    """Create a FastAPI test app instance."""
    from backend.app import app
    return app


@pytest_asyncio.fixture(scope="function")
async def client(test_app):
    """Create an async httpx test client for FastAPI.

    Uses httpx.AsyncClient with ASGITransport for compatibility
    with httpx 0.28+ and starlette 0.35.
    """
    import httpx

    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture
def auth_headers():
    """Return valid Basic Auth headers for testing."""
    import base64
    credentials = base64.b64encode(b"testuser:testpassword").decode()
    return {"Authorization": f"Basic {credentials}"}


@pytest.fixture
def jwt_token():
    """Return a valid JWT token for testing."""
    from backend.utils.auth import create_access_token
    token, _ = create_access_token("testuser")
    return token


@pytest.fixture
def jwt_headers(jwt_token):
    """Return valid JWT Bearer headers for testing."""
    return {"Authorization": f"Bearer {jwt_token}"}


@pytest.fixture
def mock_claude():
    """Mock the Claude API client to prevent real API calls."""
    with patch("agents.base_agent.Anthropic") as mock:
        yield mock
