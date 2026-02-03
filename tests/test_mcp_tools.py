"""
MCP Tools Integration Tests

Tests for MCP client methods, error handling, and server tool definitions.
Covers both existing and new tools added in feature/mcp-new-tools.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Check if MCP module is available (not installed in CI)
MCP_AVAILABLE = False
try:
    mcp_path = os.path.join(os.path.dirname(__file__), '..', 'mcp')
    if mcp_path not in sys.path:
        sys.path.insert(0, mcp_path)
    from confluence_client import ConfluenceClient
    MCP_AVAILABLE = True
except ImportError:
    pass

requires_mcp = pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP module not available")


# ============================================================================
# A. Client method tests — verify correct endpoint and params
# ============================================================================

@requires_mcp
class TestClientMethods:
    """Test that each client method calls the correct endpoint."""

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def _make_client(self):
        return ConfluenceClient(base_url="http://test:8000")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_latest_synthesis(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={"id": 1}) as mock:
            result = client.get_latest_synthesis()
            mock.assert_called_once_with("GET", "/api/synthesis/latest")
            assert result == {"id": 1}

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_synthesis_history_default(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value=[]) as mock:
            client.get_synthesis_history()
            mock.assert_called_once_with("GET", "/api/synthesis/history?limit=5")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_synthesis_history_with_offset(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value=[]) as mock:
            client.get_synthesis_history(limit=10, offset=20)
            mock.assert_called_once_with("GET", "/api/synthesis/history?limit=10&offset=20")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_synthesis_by_id(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={"id": 42}) as mock:
            result = client.get_synthesis_by_id(42)
            mock.assert_called_once_with("GET", "/api/synthesis/42")
            assert result["id"] == 42

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_quality_trends(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={}) as mock:
            client.get_quality_trends(days=14)
            mock.assert_called_once_with("GET", "/api/quality/trends?days=14")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_quality_flagged(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={}) as mock:
            client.get_quality_flagged(limit=5)
            mock.assert_called_once_with("GET", "/api/quality/flagged?limit=5")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_source_health(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={}) as mock:
            client.get_source_health()
            mock.assert_called_once_with("GET", "/api/health/sources")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_active_alerts_default(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={}) as mock:
            client.get_active_alerts()
            mock.assert_called_once_with("GET", "/api/health/alerts?include_acknowledged=false")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_active_alerts_include_acknowledged(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={}) as mock:
            client.get_active_alerts(include_acknowledged=True)
            mock.assert_called_once_with("GET", "/api/health/alerts?include_acknowledged=true")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_theme_evolution(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={}) as mock:
            client.get_theme_evolution(theme_id=7)
            mock.assert_called_once_with("GET", "/api/dashboard/historical/7")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_synthesis_quality_latest(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={}) as mock:
            client.get_synthesis_quality()
            mock.assert_called_once_with("GET", "/api/quality/latest")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_synthesis_quality_by_id(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={}) as mock:
            client.get_synthesis_quality(synthesis_id=5)
            mock.assert_called_once_with("GET", "/api/quality/5")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_all_symbols(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={"symbols": []}) as mock:
            client.get_all_symbols()
            mock.assert_called_once_with("GET", "/api/symbols")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_get_symbol_detail(self):
        client = self._make_client()
        with patch.object(client, '_request', return_value={}) as mock:
            client.get_symbol_detail("SPX")
            mock.assert_called_once_with("GET", "/api/symbols/SPX")


# ============================================================================
# B. Error handling tests
# ============================================================================

@requires_mcp
class TestClientErrors:
    """Test error handling in the client."""

    def test_missing_credentials_raises_value_error(self):
        """Client requires CONFLUENCE_USERNAME and CONFLUENCE_PASSWORD."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the env vars if set
            os.environ.pop("CONFLUENCE_USERNAME", None)
            os.environ.pop("CONFLUENCE_PASSWORD", None)
            with pytest.raises(ValueError, match="CONFLUENCE_USERNAME"):
                ConfluenceClient(base_url="http://test:8000")

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_request_exception_propagates(self):
        """HTTP errors from _request should propagate."""
        client = ConfluenceClient(base_url="http://test:8000")
        with patch.object(client, '_request', side_effect=Exception("Connection refused")):
            with pytest.raises(Exception, match="Connection refused"):
                client.get_latest_synthesis()

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_search_content_catches_exceptions(self):
        """search_content wraps exceptions instead of raising."""
        client = ConfluenceClient(base_url="http://test:8000")
        with patch.object(client, '_request', side_effect=Exception("timeout")):
            result = client.search_content("test query")
            assert len(result) == 1
            assert "error" in result[0]
            assert "timeout" in result[0]["error"]

    @patch.dict(os.environ, {"CONFLUENCE_USERNAME": "test", "CONFLUENCE_PASSWORD": "test"})
    def test_search_content_normalizes_results(self):
        """search_content normalizes API results to consistent format."""
        client = ConfluenceClient(base_url="http://test:8000")
        api_response = {
            "results": [
                {
                    "id": 1,
                    "source": "youtube",
                    "title": "Test Video",
                    "date": "2025-01-01",
                    "type": "video",
                    "themes": ["macro"],
                    "sentiment": "bullish",
                    "conviction": 0.8,
                    "analysis_summary": "Summary text"
                }
            ]
        }
        with patch.object(client, '_request', return_value=api_response):
            result = client.search_content("test")
            assert len(result) == 1
            assert result[0]["id"] == 1
            assert result[0]["summary"] == "Summary text"


# ============================================================================
# C. Server tool definition tests — verify tools exist in server.py source
# ============================================================================

@requires_mcp
class TestServerToolDefinitions:
    """Verify new tools are defined in server.py by reading the source."""

    @classmethod
    def setup_class(cls):
        """Read server.py source once for all tests."""
        server_path = os.path.join(os.path.dirname(__file__), '..', 'mcp', 'server.py')
        with open(server_path, 'r') as f:
            cls.server_source = f.read()

    def test_get_synthesis_history_tool_defined(self):
        assert 'name="get_synthesis_history"' in self.server_source

    def test_get_synthesis_by_id_tool_defined(self):
        assert 'name="get_synthesis_by_id"' in self.server_source

    def test_get_quality_trends_tool_defined(self):
        assert 'name="get_quality_trends"' in self.server_source

    def test_get_quality_flagged_tool_defined(self):
        assert 'name="get_quality_flagged"' in self.server_source

    def test_get_system_health_tool_defined(self):
        assert 'name="get_system_health"' in self.server_source

    def test_get_active_alerts_tool_defined(self):
        assert 'name="get_active_alerts"' in self.server_source

    def test_get_theme_evolution_tool_defined(self):
        assert 'name="get_theme_evolution"' in self.server_source

    def test_synthesis_id_required_error_handling(self):
        """Verify synthesis_id required check exists in handler."""
        assert 'synthesis_id is required' in self.server_source

    def test_theme_id_required_error_handling(self):
        """Verify theme_id required check exists in handler."""
        assert 'theme_id is required' in self.server_source

    def test_int_type_validation_exists(self):
        """Verify int() type conversion is used for ID params."""
        # Multiple handlers use int() for type safety
        assert 'int(synthesis_id)' in self.server_source
        assert 'int(theme_id)' in self.server_source
