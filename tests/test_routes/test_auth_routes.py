"""Behavioral tests for authentication routes."""
import pytest

pytestmark = pytest.mark.asyncio


class TestAuthLogin:
    """Test POST /api/auth/login."""

    async def test_login_with_valid_credentials(self, client):
        response = await client.post(
            "/api/auth/login",
            json={"username": "testuser", "password": "testpassword"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "expires_at" in data
        assert "username" in data

    async def test_login_with_invalid_credentials(self, client):
        response = await client.post(
            "/api/auth/login",
            json={"username": "wrong", "password": "wrong"},
        )
        assert response.status_code == 401

    async def test_login_with_no_body(self, client):
        response = await client.post("/api/auth/login")
        assert response.status_code == 422

    async def test_jwt_token_works_for_protected_endpoint(self, client, jwt_headers):
        response = await client.get("/api/synthesis/latest", headers=jwt_headers)
        # Should not be 401 (may be 404 if no synthesis exists)
        assert response.status_code != 401

    async def test_expired_token_rejected(self, client):
        import jwt
        from datetime import datetime, timedelta, timezone

        expired_payload = {
            "sub": "testuser",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "type": "access",
        }
        expired_token = jwt.encode(
            expired_payload, "test-jwt-secret", algorithm="HS256"
        )
        response = await client.get(
            "/api/synthesis/latest",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401

    async def test_basic_auth_works_for_protected_endpoint(self, client, auth_headers):
        response = await client.get("/api/synthesis/latest", headers=auth_headers)
        # Should not be 401 (may be 404 if no synthesis exists)
        assert response.status_code != 401
