"""
Tests for PRD-047: Data Integrity & Resilience

Tests for:
- Safe analysis_result access helpers
- Synthesis generation timeout
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from backend.utils.data_helpers import (
    safe_get_analysis_result,
    safe_get_analysis_preview,
    get_analysis_field,
    safe_json_loads
)


class TestSafeGetAnalysisResult:
    """Tests for safe_get_analysis_result() helper."""

    def test_with_none_content(self):
        """Test with None content object."""
        result = safe_get_analysis_result(None)
        assert result == {}

    def test_with_none_analysis_result(self):
        """Test with content that has None analysis_result."""
        content = Mock(analysis_result=None)
        result = safe_get_analysis_result(content)
        assert result == {}

    def test_with_dict_analysis_result(self):
        """Test with analysis_result that's already a dict."""
        content = Mock(analysis_result={"sentiment": "bullish", "themes": ["tech"]})
        result = safe_get_analysis_result(content)
        assert result["sentiment"] == "bullish"
        assert result["themes"] == ["tech"]

    def test_with_json_string_analysis_result(self):
        """Test with analysis_result as JSON string."""
        content = Mock(analysis_result='{"sentiment": "bullish", "conviction": 8}')
        result = safe_get_analysis_result(content)
        assert result["sentiment"] == "bullish"
        assert result["conviction"] == 8

    def test_with_invalid_json_string(self):
        """Test with invalid JSON string returns raw in dict."""
        content = Mock(analysis_result="not valid json {")
        result = safe_get_analysis_result(content)
        assert "raw" in result
        assert "not valid json" in result["raw"]

    def test_with_max_length_on_invalid_json(self):
        """Test max_length truncates raw string."""
        long_text = "x" * 1000
        content = Mock(analysis_result=long_text)
        result = safe_get_analysis_result(content, max_length=100)
        assert "raw" in result
        assert len(result["raw"]) == 100


class TestSafeGetAnalysisPreview:
    """Tests for safe_get_analysis_preview() helper."""

    def test_with_none_content(self):
        """Test with None content object."""
        result = safe_get_analysis_preview(None)
        assert result == "[Not analyzed]"

    def test_with_none_analysis_result(self):
        """Test with content that has None analysis_result."""
        content = Mock(analysis_result=None)
        result = safe_get_analysis_preview(content)
        assert result == "[Not analyzed]"

    def test_with_short_string(self):
        """Test with string shorter than max_length."""
        content = Mock(analysis_result="Short analysis text")
        result = safe_get_analysis_preview(content, max_length=500)
        assert result == "Short analysis text"

    def test_with_long_string_truncates(self):
        """Test that long strings are truncated."""
        content = Mock(analysis_result="x" * 1000)
        result = safe_get_analysis_preview(content, max_length=100)
        assert len(result) == 103  # 100 chars + "..."
        assert result.endswith("...")

    def test_with_dict_converts_to_string(self):
        """Test that dict is converted to JSON string."""
        content = Mock(analysis_result={"key": "value"})
        result = safe_get_analysis_preview(content)
        assert '{"key": "value"}' == result

    def test_default_max_length(self):
        """Test default max_length is 500."""
        content = Mock(analysis_result="y" * 600)
        result = safe_get_analysis_preview(content)
        assert len(result) == 503  # 500 + "..."


class TestGetAnalysisField:
    """Tests for get_analysis_field() helper."""

    def test_with_none_content(self):
        """Test with None content returns default."""
        result = get_analysis_field(None, "sentiment", "neutral")
        assert result == "neutral"

    def test_with_none_analysis_result(self):
        """Test with None analysis_result returns default."""
        content = Mock(analysis_result=None)
        result = get_analysis_field(content, "sentiment", "neutral")
        assert result == "neutral"

    def test_with_missing_field(self):
        """Test with missing field returns default."""
        content = Mock(analysis_result={"themes": []})
        result = get_analysis_field(content, "sentiment", "neutral")
        assert result == "neutral"

    def test_with_existing_field(self):
        """Test with existing field returns value."""
        content = Mock(analysis_result={"sentiment": "bullish"})
        result = get_analysis_field(content, "sentiment", "neutral")
        assert result == "bullish"

    def test_with_json_string(self):
        """Test with JSON string analysis_result."""
        content = Mock(analysis_result='{"conviction": 9}')
        result = get_analysis_field(content, "conviction", 0)
        assert result == 9

    def test_with_invalid_json_returns_default(self):
        """Test with invalid JSON returns default."""
        content = Mock(analysis_result="not json")
        result = get_analysis_field(content, "field", "default")
        assert result == "default"

    def test_default_is_none(self):
        """Test that default defaults to None."""
        content = Mock(analysis_result={})
        result = get_analysis_field(content, "missing")
        assert result is None


class TestSafeJsonLoads:
    """Tests for safe_json_loads() helper."""

    def test_with_none(self):
        """Test with None returns default."""
        result = safe_json_loads(None)
        assert result == {}

    def test_with_empty_string(self):
        """Test with empty string returns default."""
        result = safe_json_loads("")
        assert result == {}

    def test_with_valid_json(self):
        """Test with valid JSON returns parsed dict."""
        result = safe_json_loads('{"key": "value"}')
        assert result == {"key": "value"}

    def test_with_invalid_json(self):
        """Test with invalid JSON returns default."""
        result = safe_json_loads("not json", {"default": True})
        assert result == {"default": True}

    def test_with_dict_input(self):
        """Test with dict input returns it unchanged."""
        input_dict = {"already": "dict"}
        result = safe_json_loads(input_dict)
        assert result == input_dict

    def test_with_json_array(self):
        """Test with JSON array returns default (expects dict)."""
        result = safe_json_loads("[1, 2, 3]", {"default": True})
        assert result == {"default": True}


class TestSynthesisTimeoutConfiguration:
    """Tests for synthesis timeout configuration."""

    def test_timeout_constant_exists(self):
        """Test that SYNTHESIS_TIMEOUT_SECONDS is defined."""
        from backend.routes.synthesis import SYNTHESIS_TIMEOUT_SECONDS
        assert isinstance(SYNTHESIS_TIMEOUT_SECONDS, int)
        assert SYNTHESIS_TIMEOUT_SECONDS > 0

    def test_default_timeout_is_120(self):
        """Test default timeout is 120 seconds."""
        import os
        # Remove env var if set
        original = os.environ.pop("SYNTHESIS_TIMEOUT", None)
        try:
            # Re-import to get default
            import importlib
            import backend.routes.synthesis as syn
            importlib.reload(syn)
            assert syn.SYNTHESIS_TIMEOUT_SECONDS == 120
        finally:
            if original:
                os.environ["SYNTHESIS_TIMEOUT"] = original

    def test_executor_exists(self):
        """Test that synthesis_executor ThreadPoolExecutor exists."""
        from backend.routes.synthesis import synthesis_executor
        assert synthesis_executor is not None


class TestNoUncheckedAnalysisAccess:
    """Tests to verify no unsafe analysis_result access patterns remain."""

    def test_no_direct_subscript_access(self):
        """Verify no code uses .analysis_result[ directly without guard."""
        import subprocess
        import os

        # Check backend directory
        result = subprocess.run(
            ['grep', '-rn', r'\.analysis_result\[', '--include=*.py', 'backend/'],
            capture_output=True, text=True, cwd=os.getcwd()
        )
        # Filter out test files and comments
        lines = [l for l in result.stdout.strip().split('\n')
                 if l and 'test_' not in l and '# ' not in l.split(':', 2)[-1]]

        # All remaining should have guards (if x else y pattern)
        for line in lines:
            assert ' if ' in line or 'safe_get' in line, f"Unsafe access: {line}"

    def test_data_helpers_imported_in_synthesis(self):
        """Verify data_helpers is imported in synthesis.py."""
        with open('backend/routes/synthesis.py', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'from backend.utils.data_helpers import' in content

    def test_data_helpers_imported_in_trigger(self):
        """Verify data_helpers is imported in trigger.py."""
        with open('backend/routes/trigger.py', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'from backend.utils.data_helpers import' in content

    def test_data_helpers_imported_in_scheduler(self):
        """Verify data_helpers is imported in scheduler.py."""
        with open('backend/scheduler.py', 'r', encoding='utf-8') as f:
            content = f.read()
        assert 'from backend.utils.data_helpers import' in content
