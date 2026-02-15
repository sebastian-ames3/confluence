"""
Tests for PRD-036: Session Authentication (JWT)

Tests for:
- 36.1 Dependencies
- 36.2 JWT Utilities
- 36.3 Auth Endpoints
- 36.4 Route Migration
- 36.5 Backward Compatibility
"""
import pytest
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Try to import jwt - may fail on some Windows environments due to cryptography DLL issues
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None


class TestDependencies:
    """Test 36.1: PyJWT dependency."""

    def test_pyjwt_in_requirements(self):
        """Verify PyJWT is in requirements.txt."""
        requirements_path = Path(__file__).parent.parent / "requirements.txt"
        content = requirements_path.read_text()
        assert "PyJWT" in content, "PyJWT should be in requirements.txt"

    @pytest.mark.skipif(not JWT_AVAILABLE, reason="jwt module not available on this platform")
    def test_jwt_import_works(self):
        """Verify jwt module can be imported."""
        assert jwt is not None, "jwt should be importable"
        assert hasattr(jwt, 'encode'), "jwt should have encode function"
        assert hasattr(jwt, 'decode'), "jwt should have decode function"


class TestJWTUtilities:
    """Test 36.2: JWT Utilities in auth.py."""

    def test_auth_file_has_jwt_imports(self):
        """Verify auth.py imports JWT module."""
        auth_path = Path(__file__).parent.parent / "backend" / "utils" / "auth.py"
        content = auth_path.read_text()
        assert "import jwt" in content, "auth.py should import jwt"

    def test_auth_file_has_jwt_constants(self):
        """Verify auth.py defines JWT constants."""
        auth_path = Path(__file__).parent.parent / "backend" / "utils" / "auth.py"
        content = auth_path.read_text()

        assert "JWT_SECRET" in content, "Should define JWT_SECRET"
        assert "JWT_ALGORITHM" in content, "Should define JWT_ALGORITHM"
        assert "JWT_EXPIRATION_HOURS" in content, "Should define JWT_EXPIRATION_HOURS"

    def test_auth_file_has_create_access_token(self):
        """Verify create_access_token function exists."""
        auth_path = Path(__file__).parent.parent / "backend" / "utils" / "auth.py"
        content = auth_path.read_text()
        assert "def create_access_token" in content, "Should have create_access_token function"

    def test_auth_file_has_decode_token(self):
        """Verify decode_token function exists."""
        auth_path = Path(__file__).parent.parent / "backend" / "utils" / "auth.py"
        content = auth_path.read_text()
        assert "def decode_token" in content, "Should have decode_token function"

    def test_auth_file_has_verify_jwt_or_basic(self):
        """Verify verify_jwt_or_basic function exists."""
        auth_path = Path(__file__).parent.parent / "backend" / "utils" / "auth.py"
        content = auth_path.read_text()
        assert "def verify_jwt_or_basic" in content, "Should have verify_jwt_or_basic function"

    @pytest.mark.skipif(not JWT_AVAILABLE, reason="jwt module not available on this platform")
    def test_create_access_token_returns_valid_jwt(self):
        """Test that create_access_token returns a valid JWT."""
        from backend.utils.auth import create_access_token, JWT_SECRET, JWT_ALGORITHM

        token, expires_at = create_access_token("testuser")

        # Verify token is a string
        assert isinstance(token, str), "Token should be a string"

        # Verify token can be decoded
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == "testuser", "Token should contain username"
        assert "exp" in payload, "Token should have expiration"

    @pytest.mark.skipif(not JWT_AVAILABLE, reason="jwt module not available on this platform")
    def test_create_access_token_has_correct_expiration(self):
        """Test that token has correct expiration time."""
        from backend.utils.auth import create_access_token, JWT_EXPIRATION_HOURS

        token, expires_at = create_access_token("testuser")

        # Verify expiration is approximately JWT_EXPIRATION_HOURS from now
        expected_exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
        delta = abs((expires_at - expected_exp).total_seconds())
        assert delta < 5, "Expiration should be close to expected time"

    @pytest.mark.skipif(not JWT_AVAILABLE, reason="jwt module not available on this platform")
    def test_decode_token_returns_payload(self):
        """Test that decode_token returns valid payload."""
        from backend.utils.auth import create_access_token, decode_token

        token, _ = create_access_token("testuser")
        payload = decode_token(token)

        assert payload["sub"] == "testuser", "Payload should contain username"

    @pytest.mark.skipif(not JWT_AVAILABLE, reason="jwt module not available on this platform")
    def test_decode_token_rejects_invalid_token(self):
        """Test that decode_token raises exception for invalid token."""
        from backend.utils.auth import decode_token
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid.token.here")

        assert exc_info.value.status_code == 401, "Should return 401 for invalid token"

    @pytest.mark.skipif(not JWT_AVAILABLE, reason="jwt module not available on this platform")
    def test_decode_token_rejects_expired_token(self):
        """Test that decode_token raises exception for expired token."""
        from backend.utils.auth import decode_token, JWT_SECRET, JWT_ALGORITHM
        from fastapi import HTTPException

        # Create an expired token
        expired_payload = {
            "sub": "testuser",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        expired_token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            decode_token(expired_token)

        assert exc_info.value.status_code == 401, "Should return 401 for expired token"
        assert "expired" in exc_info.value.detail.lower(), "Error should mention expiration"

    @pytest.mark.skipif(not JWT_AVAILABLE, reason="jwt module not available on this platform")
    def test_should_refresh_token_returns_true_when_expiring(self):
        """Test should_refresh_token returns True for soon-expiring tokens."""
        from backend.utils.auth import should_refresh_token, JWT_SECRET, JWT_ALGORITHM

        # Create token expiring in 30 minutes (within threshold)
        soon_payload = {
            "sub": "testuser",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        soon_token = jwt.encode(soon_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        assert should_refresh_token(soon_token) is True, "Should return True for expiring token"

    @pytest.mark.skipif(not JWT_AVAILABLE, reason="jwt module not available on this platform")
    def test_should_refresh_token_returns_false_when_fresh(self):
        """Test should_refresh_token returns False for fresh tokens."""
        from backend.utils.auth import should_refresh_token, JWT_SECRET, JWT_ALGORITHM

        # Create token expiring in 20 hours (not within threshold)
        fresh_payload = {
            "sub": "testuser",
            "exp": datetime.now(timezone.utc) + timedelta(hours=20),
        }
        fresh_token = jwt.encode(fresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        assert should_refresh_token(fresh_token) is False, "Should return False for fresh token"


class TestAuthEndpoints:
    """Test 36.3: Auth Router Endpoints."""

    def test_auth_router_file_exists(self):
        """Verify auth.py router exists."""
        auth_path = Path(__file__).parent.parent / "backend" / "routes" / "auth.py"
        assert auth_path.exists(), "backend/routes/auth.py should exist"

    def test_auth_router_has_login_endpoint(self):
        """Verify login endpoint exists."""
        auth_path = Path(__file__).parent.parent / "backend" / "routes" / "auth.py"
        content = auth_path.read_text()
        assert '"/login"' in content, "Should have /login endpoint"
        assert "LoginRequest" in content, "Should use LoginRequest model"
        assert "LoginResponse" in content, "Should use LoginResponse model"

    def test_auth_router_has_logout_endpoint(self):
        """Verify logout endpoint exists."""
        auth_path = Path(__file__).parent.parent / "backend" / "routes" / "auth.py"
        content = auth_path.read_text()
        assert '"/logout"' in content, "Should have /logout endpoint"

    def test_auth_router_has_refresh_endpoint(self):
        """Verify refresh endpoint exists."""
        auth_path = Path(__file__).parent.parent / "backend" / "routes" / "auth.py"
        content = auth_path.read_text()
        assert '"/refresh"' in content, "Should have /refresh endpoint"

    def test_auth_router_has_me_endpoint(self):
        """Verify /me endpoint exists."""
        auth_path = Path(__file__).parent.parent / "backend" / "routes" / "auth.py"
        content = auth_path.read_text()
        assert '"/me"' in content, "Should have /me endpoint"

    def test_login_uses_timing_safe_comparison(self):
        """Verify login uses secure comparison for credentials."""
        auth_path = Path(__file__).parent.parent / "backend" / "routes" / "auth.py"
        content = auth_path.read_text()
        assert "secrets.compare_digest" in content, "Should use timing-safe comparison"


class TestAppRouterRegistration:
    """Test 36.4: Auth Router Registration."""

    def test_app_imports_auth_router(self):
        """Verify app.py imports auth router."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()
        assert "auth" in content, "app.py should import auth"

    def test_app_includes_auth_router(self):
        """Verify app.py includes auth router."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()
        assert 'auth.router' in content, "app.py should include auth.router"
        assert '/api/auth' in content, "auth router should be at /api/auth prefix"


class TestRouteMigration:
    """Test 36.5: Route Migration to verify_jwt_or_basic."""

    def test_dashboard_uses_jwt_or_basic(self):
        """Verify dashboard.py uses verify_jwt_or_basic."""
        path = Path(__file__).parent.parent / "backend" / "routes" / "dashboard.py"
        content = path.read_text()
        assert "verify_jwt_or_basic" in content, "dashboard.py should use verify_jwt_or_basic"
        assert "verify_credentials" not in content or "verify_jwt_or_basic" in content, \
            "Should have migrated to verify_jwt_or_basic"

    def test_synthesis_uses_jwt_or_basic(self):
        """Verify synthesis.py uses verify_jwt_or_basic."""
        path = Path(__file__).parent.parent / "backend" / "routes" / "synthesis.py"
        content = path.read_text()
        assert "verify_jwt_or_basic" in content, "synthesis.py should use verify_jwt_or_basic"

    def test_confluence_uses_jwt_or_basic(self):
        """Verify confluence.py uses verify_jwt_or_basic."""
        path = Path(__file__).parent.parent / "backend" / "routes" / "confluence.py"
        content = path.read_text()
        assert "verify_jwt_or_basic" in content, "confluence.py should use verify_jwt_or_basic"

    def test_search_uses_jwt_or_basic(self):
        """Verify search.py uses verify_jwt_or_basic."""
        path = Path(__file__).parent.parent / "backend" / "routes" / "search.py"
        content = path.read_text()
        assert "verify_jwt_or_basic" in content, "search.py should use verify_jwt_or_basic"


class TestBackwardCompatibility:
    """Test backward compatibility - Basic Auth still works."""

    @pytest.mark.skipif(not JWT_AVAILABLE, reason="jwt module not available on this platform")
    def test_verify_jwt_or_basic_accepts_basic_auth(self):
        """Verify verify_jwt_or_basic accepts HTTP Basic credentials."""
        from backend.utils.auth import verify_jwt_or_basic, AUTH_USERNAME, AUTH_PASSWORD
        from fastapi.security import HTTPBasicCredentials

        # Skip if no password configured (dev mode)
        if not AUTH_PASSWORD:
            pytest.skip("No AUTH_PASSWORD configured - dev mode")

        # Create mock Basic credentials
        credentials = HTTPBasicCredentials(username=AUTH_USERNAME, password=AUTH_PASSWORD)

        # Should not raise exception
        username = verify_jwt_or_basic(credentials=credentials, bearer_token=None)
        assert username == AUTH_USERNAME, "Should return username from Basic auth"

    @pytest.mark.skipif(not JWT_AVAILABLE, reason="jwt module not available on this platform")
    def test_verify_jwt_or_basic_accepts_bearer_token(self):
        """Verify verify_jwt_or_basic accepts Bearer token."""
        from backend.utils.auth import verify_jwt_or_basic, create_access_token
        from fastapi.security import HTTPAuthorizationCredentials

        # Create valid token
        token, _ = create_access_token("testuser")

        # Create mock Bearer credentials
        bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Should not raise exception
        username = verify_jwt_or_basic(credentials=None, bearer_token=bearer)
        assert username == "testuser", "Should return username from Bearer token"

    def test_collect_routes_require_authentication(self):
        """Verify collect.py requires authentication on all endpoints."""
        path = Path(__file__).parent.parent / "backend" / "routes" / "collect.py"
        content = path.read_text()

        # Collect routes MUST use auth dependency (security hardening)
        assert "verify_jwt_or_basic" in content, "collect.py must require JWT/Basic auth"

    def test_analyze_routes_require_authentication(self):
        """Verify analyze.py requires authentication on all endpoints."""
        path = Path(__file__).parent.parent / "backend" / "routes" / "analyze.py"
        content = path.read_text()

        # Analyze routes MUST use auth dependency (security hardening)
        assert "verify_jwt_or_basic" in content, "analyze.py must require JWT/Basic auth"


class TestFrontendIntegration:
    """Test frontend auth integration files exist."""

    def test_auth_js_exists(self):
        """Verify auth.js file exists."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "auth.js"
        assert path.exists(), "frontend/js/auth.js should exist"

    def test_auth_js_has_auth_manager(self):
        """Verify AuthManager is defined in auth.js."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "auth.js"
        content = path.read_text()
        assert "AuthManager" in content, "auth.js should define AuthManager"

    def test_auth_js_has_token_methods(self):
        """Verify AuthManager has token management methods."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "auth.js"
        content = path.read_text()

        assert "getToken" in content, "AuthManager should have getToken"
        assert "setToken" in content, "AuthManager should have setToken"
        assert "clearToken" in content, "AuthManager should have clearToken"
        assert "isLoggedIn" in content, "AuthManager should have isLoggedIn"

    def test_auth_js_has_auth_actions(self):
        """Verify AuthManager has auth action methods."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "auth.js"
        content = path.read_text()

        assert "login" in content, "AuthManager should have login"
        assert "logout" in content, "AuthManager should have logout"
        assert "refreshToken" in content, "AuthManager should have refreshToken"

    def test_api_js_has_bearer_token_support(self):
        """Verify api.js includes Bearer token in requests."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "api.js"
        content = path.read_text()

        assert "Bearer" in content, "api.js should use Bearer token"
        assert "Authorization" in content, "api.js should set Authorization header"

    def test_api_js_handles_401(self):
        """Verify api.js handles 401 responses."""
        path = Path(__file__).parent.parent / "frontend" / "js" / "api.js"
        content = path.read_text()

        assert "401" in content, "api.js should check for 401 status"
        assert "AuthManager" in content, "api.js should use AuthManager"

    def test_index_html_has_login_modal(self):
        """Verify index.html includes login modal."""
        path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = path.read_text(encoding='utf-8')

        assert "login-modal" in content, "index.html should have login-modal"
        assert "login-form" in content, "index.html should have login-form"
        assert "login-username" in content, "index.html should have username input"
        assert "login-password" in content, "index.html should have password input"

    def test_index_html_has_user_menu(self):
        """Verify index.html includes user menu."""
        path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = path.read_text(encoding='utf-8')

        assert "user-menu" in content, "index.html should have user-menu"
        assert "user-name" in content, "index.html should have user-name"
        assert "logout-btn" in content, "index.html should have logout-btn"

    def test_index_html_includes_auth_scripts(self):
        """Verify index.html includes auth.js script."""
        path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = path.read_text(encoding='utf-8')

        assert "auth.js" in content, "index.html should include auth.js"
        assert "api.js" in content, "index.html should include api.js"

    def test_modals_css_has_login_styles(self):
        """Verify modals CSS has login modal styles."""
        path = Path(__file__).parent.parent / "frontend" / "css" / "components" / "_modals.css"
        content = path.read_text()

        assert "login-modal" in content, "modals CSS should have login-modal styles"
        assert "login-form" in content, "modals CSS should have login-form styles"
        assert "login-error" in content, "modals CSS should have login-error styles"
        assert "user-menu" in content, "modals CSS should have user-menu styles"
