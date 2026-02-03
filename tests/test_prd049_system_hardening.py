"""
Tests for PRD-049: System Hardening

Covers:
- MCP tool error handling
- CSS responsive breakpoints
- Datetime consistency
- MCP logging
- Extract function type validation
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Check if MCP module is available (not installed in CI)
MCP_AVAILABLE = False
try:
    # Add mcp directory to path for imports
    mcp_path = os.path.join(os.path.dirname(__file__), '..', 'mcp')
    if mcp_path not in sys.path:
        sys.path.insert(0, mcp_path)
    from confluence_client import (
        extract_source_breakdowns,
        extract_confluence_zones,
        extract_conflicts,
        extract_attention_priorities,
        extract_catalyst_calendar,
        extract_executive_summary,
    )
    MCP_AVAILABLE = True
except ImportError:
    pass

# Skip decorator for MCP-dependent tests
requires_mcp = pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP module not available")


# =============================================================================
# MCP Tool Error Handling Tests
# =============================================================================

class TestMCPToolErrorHandling:
    """Test that MCP tools have proper error handling."""

    def test_mcp_theme_tools_have_try_catch(self):
        """Theme tools should have try/catch blocks."""
        with open("mcp/server.py", "r", encoding="utf-8") as f:
            source = f.read()

        assert 'get_themes failed' in source, "get_themes should have error handling"
        assert 'get_active_themes failed' in source, "get_active_themes should have error handling"
        assert 'get_theme_detail failed' in source, "get_theme_detail should have error handling"

    def test_mcp_symbol_tools_have_try_catch(self):
        """Symbol tools should have try/catch blocks."""
        with open("mcp/server.py", "r", encoding="utf-8") as f:
            source = f.read()

        assert 'get_symbol_analysis failed' in source, "get_symbol_analysis should have error handling"
        assert 'get_symbol_levels failed' in source, "get_symbol_levels should have error handling"
        assert 'get_trade_setup failed' in source, "get_trade_setup should have error handling"

    def test_mcp_quality_tool_has_type_validation(self):
        """Quality tool should validate synthesis_id type."""
        with open("mcp/server.py", "r", encoding="utf-8") as f:
            source = f.read()

        assert 'synthesis_id must be an integer' in source, \
            "Quality tool should validate synthesis_id type"

    def test_mcp_theme_id_explicit_none_check(self):
        """Theme detail should use explicit None check for theme_id."""
        with open("mcp/server.py", "r", encoding="utf-8") as f:
            source = f.read()

        assert 'theme_id is None' in source, \
            "Should use explicit None check (0 is valid but falsy)"


# =============================================================================
# CSS Tests
# =============================================================================

class TestCSSResponsiveBreakpoints:
    """Test CSS responsive breakpoints."""

    def test_cards_css_has_responsive_max_height(self):
        """Cards CSS should have responsive max-height for expanded details."""
        with open("frontend/css/components/_cards.css", "r") as f:
            content = f.read()

        assert "max-height: 400px" in content, "Should have mobile max-height"
        assert "max-height: 500px" in content, "Should have tablet max-height"
        assert "max-height: 600px" in content, "Should have desktop max-height"

    def test_cards_css_uses_design_system_breakpoints(self):
        """Cards CSS should use design system breakpoints (1280px)."""
        with open("frontend/css/components/_cards.css", "r") as f:
            content = f.read()

        assert "max-width: 1280px" in content, "Should use 1280px breakpoint"

    def test_cards_css_has_firefox_scrollbar_support(self):
        """Cards CSS should have Firefox scrollbar styling."""
        with open("frontend/css/components/_cards.css", "r") as f:
            content = f.read()

        assert "scrollbar-width: thin" in content, "Should have Firefox scrollbar-width"
        assert "scrollbar-color:" in content, "Should have Firefox scrollbar-color"

    def test_cards_css_has_synced_transitions(self):
        """Icon and panel transitions should use same timing."""
        with open("frontend/css/components/_cards.css", "r") as f:
            content = f.read()

        if '.source-perspective-expand-icon' in content:
            assert 'transition-slow' not in content or 'transition-normal' in content, \
                "Transitions should be synced"


# =============================================================================
# Backend Improvements Tests
# =============================================================================

class TestDatetimeConsistency:
    """Test datetime formatting consistency."""

    def test_synthesis_agent_generated_at_have_z_suffix(self):
        """All generated_at datetime.utcnow().isoformat() calls should have Z suffix."""
        with open("agents/synthesis_agent.py", "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'generated_at' in line and 'datetime.utcnow().isoformat()' in line:
                assert '+ "Z"' in line or "+ 'Z'" in line, \
                    f"Line {i+1} missing Z suffix: {line.strip()}"


class TestNoBarExceptClauses:
    """Test no bare except clauses in synthesis agent."""

    def test_no_bare_except_clauses_in_synthesis_agent(self):
        """Synthesis agent should not have bare except clauses."""
        import inspect
        from agents.synthesis_agent import SynthesisAgent

        source = inspect.getsource(SynthesisAgent)

        lines = source.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('except:'):
                pytest.fail(f"Found bare except clause at line {i+1}: {line}")


# =============================================================================
# MCP Logging Tests
# =============================================================================

class TestMCPLogging:
    """Test MCP logging implementation."""

    def test_mcp_server_has_structured_logging(self):
        """MCP server should log tool calls with structured format."""
        with open("mcp/server.py", "r", encoding="utf-8") as f:
            source = f.read()

        assert "[MCP]" in source, "Should use [MCP] prefix for structured logging"
        assert "Tool '" in source, "Should log tool name"
        assert "called with args" in source, "Should log arguments"

    def test_mcp_server_logs_timing(self):
        """MCP server should log operation timing."""
        with open("mcp/server.py", "r", encoding="utf-8") as f:
            source = f.read()

        assert "start_time" in source, "Should track start time"
        assert "elapsed" in source or "time.time()" in source, "Should calculate elapsed time"
        assert "completed in" in source, "Should log completion time"


# =============================================================================
# Extract Function Type Validation Tests
# =============================================================================

@pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP module not available")
class TestExtractFunctionsTypeValidation:
    """Test that extract functions handle invalid input."""

    def test_extract_confluence_zones_handles_non_dict(self):
        """extract_confluence_zones should return empty list for non-dict input."""
        assert extract_confluence_zones(None) == []
        assert extract_confluence_zones("invalid") == []
        assert extract_confluence_zones([]) == []

    def test_extract_conflicts_handles_non_dict(self):
        """extract_conflicts should return empty list for non-dict input."""
        assert extract_conflicts(None) == []
        assert extract_conflicts(123) == []

    def test_extract_attention_priorities_handles_non_dict(self):
        """extract_attention_priorities should return empty list for non-dict input."""
        assert extract_attention_priorities(None) == []
        assert extract_attention_priorities({}) == []

    def test_extract_catalyst_calendar_handles_non_dict(self):
        """extract_catalyst_calendar should return empty list for non-dict input."""
        assert extract_catalyst_calendar(None) == []
        assert extract_catalyst_calendar("string") == []

    def test_extract_executive_summary_handles_non_dict(self):
        """extract_executive_summary should return empty dict for non-dict input."""
        assert extract_executive_summary(None) == {}
        assert extract_executive_summary([1, 2, 3]) == {}

    def test_extract_source_breakdowns_handles_non_dict(self):
        """extract_source_breakdowns should return empty dict for non-dict input."""
        assert extract_source_breakdowns(None) == {}
        assert extract_source_breakdowns("invalid") == {}

    def test_extract_functions_handle_missing_keys(self):
        """Extract functions should handle missing keys gracefully."""
        empty_synthesis = {}

        assert extract_confluence_zones(empty_synthesis) == []
        assert extract_conflicts(empty_synthesis) == []
        assert extract_attention_priorities(empty_synthesis) == []
        assert extract_catalyst_calendar(empty_synthesis) == []
        assert extract_executive_summary(empty_synthesis) == {}

    def test_extract_functions_handle_wrong_type_values(self):
        """Extract functions should handle wrong type values gracefully."""
        bad_synthesis = {
            "confluence_zones": "not a list",
            "conflict_watch": 123,
            "executive_summary": ["not", "a", "dict"]
        }

        assert extract_confluence_zones(bad_synthesis) == []
        assert extract_conflicts(bad_synthesis) == []
        assert extract_executive_summary(bad_synthesis) == {}

    def test_extract_source_breakdowns_returns_data(self):
        """extract_source_breakdowns should return breakdowns from synthesis."""
        synthesis = {
            "source_breakdowns": {
                "discord": {"summary": "test", "overall_bias": "bullish"},
                "youtube:Forward Guidance": {"summary": "FG summary", "overall_bias": "neutral"}
            }
        }

        result = extract_source_breakdowns(synthesis)
        assert "discord" in result
        assert "youtube:Forward Guidance" in result
        assert result["discord"]["summary"] == "test"
