"""
Pytest configuration and fixtures
"""
import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_db():
    """Provide a test database instance."""
    from backend.utils.db import get_db
    return get_db()


@pytest.fixture(scope="session")
def usage_limiter():
    """Provide a usage limiter instance."""
    from backend.utils.usage_limiter import get_usage_limiter
    return get_usage_limiter()
