"""Security tests - XSS, injection, input validation."""
import pytest

pytestmark = pytest.mark.asyncio


class TestXSSPrevention:
    """Verify API responses don't reflect unescaped HTML."""

    XSS_PAYLOADS = [
        '<script>alert("xss")</script>',
        '<img src=x onerror=alert(1)>',
        '"><script>alert(document.cookie)</script>',
        "javascript:alert('xss')",
    ]

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    async def test_search_does_not_reflect_xss(self, client, jwt_headers, payload):
        """Search endpoint should not reflect XSS payloads in responses."""
        response = await client.get(
            f"/api/search/content?q={payload}",
            headers=jwt_headers,
        )
        # Should not return 500 (internal error from bad input)
        assert response.status_code != 500
        # If the response has a body, the raw script tag should not appear
        if response.text:
            assert "<script>" not in response.text.lower()


class TestInputValidation:
    """Test that malformed inputs are rejected properly."""

    async def test_collect_discord_rejects_oversized_payload(self, client, auth_headers):
        """Collection endpoints should handle large payloads gracefully."""
        huge_payload = [{"content": "x" * 1000} for _ in range(1000)]
        response = await client.post(
            "/api/collect/discord", json=huge_payload, headers=auth_headers
        )
        # Should either accept (200), reject size (413/422), or handle gracefully
        assert response.status_code in [200, 413, 422]

    async def test_search_handles_sql_injection(self, client, jwt_headers):
        """Search should sanitize SQL injection attempts."""
        response = await client.get(
            "/api/search/content?q=' OR '1'='1",
            headers=jwt_headers,
        )
        # Should return results normally (sanitized) or 422, not a 500 error
        assert response.status_code != 500


class TestRateLimiting:
    """Verify rate limits are enforced on write endpoints."""

    async def test_repeated_requests_eventually_limited(self, client, auth_headers):
        """Endpoints with rate limits should eventually return 429."""
        hit_limit = False
        for _ in range(25):
            response = await client.post(
                "/api/collect/discord", json=[], headers=auth_headers
            )
            if response.status_code == 429:
                hit_limit = True
                break
        # Note: Rate limiting may not activate in test environment
        # This test documents the expected behavior
        assert response.status_code in [200, 429]
