"""Behavioral tests for synthesis routes."""
import pytest

pytestmark = pytest.mark.asyncio


class TestSynthesisLatest:
    """Test GET /api/synthesis/latest."""

    async def test_returns_response_with_auth(self, client, jwt_headers):
        response = await client.get("/api/synthesis/latest", headers=jwt_headers)
        # May return 200 with data or 404 if no synthesis exists
        assert response.status_code in [200, 404]

    async def test_requires_authentication(self, client):
        response = await client.get("/api/synthesis/latest")
        assert response.status_code == 401


class TestSynthesisGenerate:
    """Test POST /api/synthesis/generate."""

    async def test_requires_authentication(self, client):
        response = await client.post(
            "/api/synthesis/generate", json={"time_window": "7d"}
        )
        assert response.status_code == 401

    async def test_rejects_invalid_time_window(self, client, jwt_headers):
        response = await client.post(
            "/api/synthesis/generate",
            json={"time_window": "invalid"},
            headers=jwt_headers,
        )
        # Should reject invalid time windows
        assert response.status_code in [400, 422]


class TestSynthesisHistory:
    """Test GET /api/synthesis/history."""

    async def test_returns_list(self, client, jwt_headers):
        response = await client.get("/api/synthesis/history", headers=jwt_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    async def test_requires_authentication(self, client):
        response = await client.get("/api/synthesis/history")
        assert response.status_code == 401
