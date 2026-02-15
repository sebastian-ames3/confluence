"""Verify all endpoints require authentication."""
import pytest

pytestmark = pytest.mark.asyncio


class TestEndpointsRequireAuth:
    """Every endpoint should return 401 without credentials."""

    PROTECTED_ENDPOINTS = [
        ("GET", "/api/analyze/pending"),
        ("GET", "/api/analyze/stats"),
        ("GET", "/api/collect/status"),
        ("GET", "/api/collect/transcription-status"),
        ("GET", "/api/themes"),
        ("GET", "/api/themes/summary"),
        ("GET", "/api/health/sources"),
        ("GET", "/api/health/alerts"),
        ("GET", "/api/heartbeat/status"),
        ("GET", "/api/heartbeat/all"),
        ("GET", "/api/synthesis/latest"),
        ("GET", "/api/synthesis/history"),
        ("GET", "/api/search/content"),
        ("GET", "/api/symbols"),
        ("GET", "/api/quality/latest"),
        ("GET", "/api/dashboard/today"),
    ]

    @pytest.mark.parametrize("method,endpoint", PROTECTED_ENDPOINTS)
    async def test_endpoint_requires_auth(self, client, method, endpoint):
        """All API endpoints should return 401 without credentials."""
        if method == "GET":
            response = await client.get(endpoint)
        elif method == "POST":
            response = await client.post(endpoint)
        assert response.status_code == 401, (
            f"{method} {endpoint} returned {response.status_code} without auth"
        )
