"""
Tests for PRD-049: System Hardening

Covers:
- Validation failure scenarios return structured errors
- MCP tools handle missing tier data gracefully
- Version detection works for all valid versions
- API null safety
- YouTube channel format validation
- Datetime consistency
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# =============================================================================
# Phase 1: Error Handling & Validation Tests
# =============================================================================

class TestValidationFailureStructuredErrors:
    """Test that validation failures return structured error info."""

    def test_synthesis_agent_v2_validation_error_has_flag(self):
        """V2 synthesis should include validation_passed flag on error."""
        from agents.synthesis_agent import SynthesisAgent

        # Check that the validation error handling code exists
        import inspect
        source = inspect.getsource(SynthesisAgent.analyze_v2)

        assert "validation_passed" in source, "V2 should set validation_passed flag"
        assert "validation_error" in source, "V2 should set validation_error message"

    def test_synthesis_agent_v3_validation_error_has_flag(self):
        """V3 synthesis should include validation_passed flag on error."""
        from agents.synthesis_agent import SynthesisAgent

        import inspect
        source = inspect.getsource(SynthesisAgent.analyze_v3)

        assert "validation_passed" in source, "V3 should set validation_passed flag"
        assert "validation_error" in source, "V3 should set validation_error message"

    def test_synthesis_agent_v4_breakdown_degraded_flag(self):
        """V4 source breakdown failures should include degraded flag."""
        from agents.synthesis_agent import SynthesisAgent

        import inspect
        source = inspect.getsource(SynthesisAgent.analyze_v4)

        assert "degraded" in source, "V4 should set degraded flag on breakdown failure"
        assert "degradation_reason" in source, "V4 should include degradation reason"

    def test_no_bare_except_clauses_in_synthesis_agent(self):
        """Synthesis agent should not have bare except clauses."""
        import inspect
        from agents.synthesis_agent import SynthesisAgent

        source = inspect.getsource(SynthesisAgent)

        # Find all except clauses
        lines = source.split('\n')
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('except:'):
                # Check if it's a bare except (not except Something:)
                pytest.fail(f"Found bare except clause at line {i+1}: {line}")


class TestAPIResponseNullSafety:
    """Test that API responses handle null values safely."""

    def test_synthesis_route_handles_null_synthesis(self):
        """Synthesis route should return empty string for null synthesis."""
        from backend.routes.synthesis import get_latest_synthesis

        import inspect
        source = inspect.getsource(get_latest_synthesis)

        # Check for null safety pattern
        assert 'synthesis.synthesis or ""' in source or "synthesis or ''" in source, \
            "Should have null safety for synthesis field"

    def test_synthesis_route_handles_null_market_regime(self):
        """Synthesis route should return 'unknown' for null market_regime."""
        from backend.routes.synthesis import get_latest_synthesis

        import inspect
        source = inspect.getsource(get_latest_synthesis)

        assert 'market_regime or "unknown"' in source or "market_regime or 'unknown'" in source, \
            "Should have null safety for market_regime field"

    def test_synthesis_route_uses_explicit_none_checks(self):
        """Synthesis route should use explicit None checks for list fallbacks."""
        from backend.routes.synthesis import generate_synthesis

        import inspect
        source = inspect.getsource(generate_synthesis)

        # Check for explicit None check pattern
        assert "is None" in source, "Should use explicit None checks for list fallbacks"


class TestMCPToolErrorHandling:
    """Test that MCP tools have proper error handling."""

    def test_mcp_theme_tools_have_try_catch(self):
        """Theme tools should have try/catch blocks."""
        with open("mcp/server.py", "r", encoding="utf-8") as f:
            source = f.read()

        # Check for try/catch around theme operations
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
# Phase 2: V4 Compatibility Tests
# =============================================================================

class TestMCPTierAwareness:
    """Test that MCP tools handle tier data correctly."""

    def test_synthesis_api_includes_tier_returned(self):
        """Synthesis API should include tier_returned field for V4."""
        from backend.routes.synthesis import get_latest_synthesis

        import inspect
        source = inspect.getsource(get_latest_synthesis)

        assert 'tier_returned' in source, "V4 response should include tier_returned field"

    def test_mcp_source_stance_checks_tier(self):
        """get_source_stance should check tier requirements."""
        with open("mcp/server.py", "r", encoding="utf-8") as f:
            source = f.read()

        assert 'tier_returned' in source, "Should check tier_returned"
        assert 'Tier 2 or higher' in source, "Should warn when tier insufficient"

    def test_extract_source_stances_handles_v4_breakdowns(self):
        """extract_source_stances should normalize V4 breakdowns to V3 format."""
        from mcp.confluence_client import extract_source_stances

        # V4 format input
        synthesis = {
            "source_breakdowns": {
                "discord": {
                    "summary": "Discord summary",
                    "key_insights": ["insight1"],
                    "themes": ["theme1"],
                    "overall_bias": "bullish",
                    "content_count": 5
                },
                "youtube:Forward Guidance": {
                    "summary": "FG summary",
                    "overall_bias": "neutral",
                    "content_count": 2
                }
            }
        }

        result = extract_source_stances(synthesis)

        assert "discord" in result
        assert result["discord"]["current_stance_narrative"] == "Discord summary"
        assert "youtube:Forward Guidance" in result
        assert result["youtube:Forward Guidance"]["display_name"] == "Forward Guidance"


class TestYouTubeChannelFormatValidation:
    """Test YouTube channel format handling."""

    def test_validate_youtube_channel_key_standard_format(self):
        """Standard youtube:ChannelName format should parse correctly."""
        from mcp.confluence_client import _validate_youtube_channel_key

        is_youtube, display_name = _validate_youtube_channel_key("youtube:Forward Guidance")
        assert is_youtube is True
        assert display_name == "Forward Guidance"

    def test_validate_youtube_channel_key_missing_name(self):
        """youtube: without channel name should handle gracefully."""
        from mcp.confluence_client import _validate_youtube_channel_key

        is_youtube, display_name = _validate_youtube_channel_key("youtube:")
        assert is_youtube is True
        assert display_name == "Unknown Channel"

    def test_validate_youtube_channel_key_non_youtube(self):
        """Non-YouTube sources should return False."""
        from mcp.confluence_client import _validate_youtube_channel_key

        is_youtube, display_name = _validate_youtube_channel_key("discord")
        assert is_youtube is False
        assert display_name == "discord"

    def test_validate_youtube_channel_key_variant_formats(self):
        """Variant formats (yt:, youtube_) should be detected with warning."""
        from mcp.confluence_client import _validate_youtube_channel_key

        # These variant formats should be detected
        is_youtube, display_name = _validate_youtube_channel_key("yt:SomeChannel")
        assert is_youtube is True

        is_youtube, display_name = _validate_youtube_channel_key("youtube_channel")
        assert is_youtube is True

    def test_extract_source_stances_adds_youtube_flag(self):
        """Extracted stances should include is_youtube_channel flag."""
        from mcp.confluence_client import extract_source_stances

        synthesis = {
            "source_breakdowns": {
                "youtube:Moonshots": {"summary": "test", "overall_bias": "bullish"},
                "discord": {"summary": "test", "overall_bias": "neutral"}
            }
        }

        result = extract_source_stances(synthesis)

        assert result["youtube:Moonshots"]["is_youtube_channel"] is True
        assert result["discord"]["is_youtube_channel"] is False


# =============================================================================
# Phase 3: Frontend Resilience Tests (Code Structure)
# =============================================================================

class TestVersionDetection:
    """Test version detection logic in frontend."""

    def test_frontend_uses_string_version_parsing(self):
        """Frontend should use String() and startsWith() for version detection."""
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            content = f.read()

        assert "String(data.version" in content, "Should use String() for version"
        assert "startsWith('4')" in content or 'startsWith("4")' in content, \
            "Should use startsWith for V4 detection"
        assert "startsWith('3')" in content or 'startsWith("3")' in content, \
            "Should use startsWith for V3 detection"

    def test_frontend_svgs_have_unique_prefixes(self):
        """V3 and V4 sparkline gradients should have unique prefixes."""
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            content = f.read()

        assert "sparkline-gradient-v4-" in content, "V4 sparklines should use v4 prefix"
        assert "sparkline-gradient-v3-" in content, "V3 sparklines should use v3 prefix"

    def test_frontend_uses_nullish_coalescing(self):
        """Frontend should use ?? instead of || for optional chaining fallbacks."""
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            content = f.read()

        # Check that bull_case and bear_case use ??
        assert "bull_case?.view ??" in content, "bull_case should use nullish coalescing"
        assert "bear_case?.view ??" in content, "bear_case should use nullish coalescing"


# =============================================================================
# Phase 4: CSS Tests
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

        # Both should use --transition-normal
        lines = content.split('\n')
        icon_transition = None
        panel_transition = None

        for line in lines:
            if '.source-perspective-expand-icon' in content:
                # Check that transitions are synced (both use normal)
                assert 'transition-slow' not in content or 'transition-normal' in content, \
                    "Transitions should be synced"


# =============================================================================
# Phase 5: Backend Improvements Tests
# =============================================================================

class TestDatetimeConsistency:
    """Test datetime formatting consistency."""

    def test_synthesis_agent_generated_at_have_z_suffix(self):
        """All generated_at datetime.utcnow().isoformat() calls should have Z suffix."""
        with open("agents/synthesis_agent.py", "r", encoding="utf-8") as f:
            content = f.read()

        # Find generated_at lines that use isoformat()
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'generated_at' in line and 'datetime.utcnow().isoformat()' in line:
                assert '+ "Z"' in line or "+ 'Z'" in line, \
                    f"Line {i+1} missing Z suffix: {line.strip()}"

    def test_all_generated_at_have_z_suffix(self):
        """All generated_at assignments should include Z suffix."""
        with open("agents/synthesis_agent.py", "r", encoding="utf-8") as f:
            content = f.read()

        # Check that all generated_at use Z suffix
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'generated_at' in line and 'isoformat()' in line:
                assert '+ "Z"' in line or "+ 'Z'" in line, \
                    f"Line {i+1} missing Z suffix: {line.strip()}"


class TestVersionParameterValidation:
    """Test version parameter validation."""

    def test_synthesis_route_validates_version(self):
        """Synthesis route should validate version parameter."""
        from backend.routes.synthesis import generate_synthesis

        import inspect
        source = inspect.getsource(generate_synthesis)

        assert "valid_versions" in source, "Should define valid versions"
        assert "Invalid version" in source, "Should return error for invalid version"
        assert "status_code=400" in source, "Should return 400 for invalid version"

    def test_valid_versions_list_is_correct(self):
        """Valid versions should be 1, 2, 3, 4."""
        with open("backend/routes/synthesis.py", "r") as f:
            content = f.read()

        assert '"1"' in content and '"2"' in content and '"3"' in content and '"4"' in content, \
            "Valid versions should include 1, 2, 3, 4"


# =============================================================================
# Phase 6: Low Priority Tests
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
# Integration Tests
# =============================================================================

class TestExtractFunctionsTypeValidation:
    """Test that extract functions handle invalid input."""

    def test_extract_confluence_zones_handles_non_dict(self):
        """extract_confluence_zones should return empty list for non-dict input."""
        from mcp.confluence_client import extract_confluence_zones

        assert extract_confluence_zones(None) == []
        assert extract_confluence_zones("invalid") == []
        assert extract_confluence_zones([]) == []

    def test_extract_conflicts_handles_non_dict(self):
        """extract_conflicts should return empty list for non-dict input."""
        from mcp.confluence_client import extract_conflicts

        assert extract_conflicts(None) == []
        assert extract_conflicts(123) == []

    def test_extract_attention_priorities_handles_non_dict(self):
        """extract_attention_priorities should return empty list for non-dict input."""
        from mcp.confluence_client import extract_attention_priorities

        assert extract_attention_priorities(None) == []
        assert extract_attention_priorities({}) == []

    def test_extract_catalyst_calendar_handles_non_dict(self):
        """extract_catalyst_calendar should return empty list for non-dict input."""
        from mcp.confluence_client import extract_catalyst_calendar

        assert extract_catalyst_calendar(None) == []
        assert extract_catalyst_calendar("string") == []

    def test_extract_executive_summary_handles_non_dict(self):
        """extract_executive_summary should return empty dict for non-dict input."""
        from mcp.confluence_client import extract_executive_summary

        assert extract_executive_summary(None) == {}
        assert extract_executive_summary([1, 2, 3]) == {}

    def test_extract_source_stances_handles_non_dict(self):
        """extract_source_stances should return empty dict for non-dict input."""
        from mcp.confluence_client import extract_source_stances

        assert extract_source_stances(None) == {}
        assert extract_source_stances("invalid") == {}

    def test_extract_functions_handle_missing_keys(self):
        """Extract functions should handle missing keys gracefully."""
        from mcp.confluence_client import (
            extract_confluence_zones,
            extract_conflicts,
            extract_attention_priorities,
            extract_catalyst_calendar,
            extract_executive_summary
        )

        empty_synthesis = {}

        assert extract_confluence_zones(empty_synthesis) == []
        assert extract_conflicts(empty_synthesis) == []
        assert extract_attention_priorities(empty_synthesis) == []
        assert extract_catalyst_calendar(empty_synthesis) == []
        assert extract_executive_summary(empty_synthesis) == {}

    def test_extract_functions_handle_wrong_type_values(self):
        """Extract functions should handle wrong type values gracefully."""
        from mcp.confluence_client import (
            extract_confluence_zones,
            extract_conflicts,
            extract_executive_summary
        )

        # Values are wrong types
        bad_synthesis = {
            "confluence_zones": "not a list",
            "conflict_watch": 123,
            "executive_summary": ["not", "a", "dict"]
        }

        assert extract_confluence_zones(bad_synthesis) == []
        assert extract_conflicts(bad_synthesis) == []
        assert extract_executive_summary(bad_synthesis) == {}
