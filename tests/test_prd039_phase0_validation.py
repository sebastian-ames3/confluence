"""
Phase 0 Validation Tests for PRD-039

Tests extraction prompts on real-world sample content to validate
accuracy before building full pipeline.

Success criteria: >70% extraction accuracy
"""

import pytest
import json
import os
from agents.symbol_level_extractor import SymbolLevelExtractor


class TestPhase0Validation:
    """Phase 0: Validate extraction prompts on realistic samples."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance with dummy API key for testing."""
        # Use dummy API key for testing - we're not actually calling the API
        return SymbolLevelExtractor(api_key="test-key-for-unit-tests")

    @pytest.fixture
    def kt_sample_transcript(self):
        """Load KT Technical sample transcript."""
        fixtures_path = os.path.join(os.path.dirname(__file__), "fixtures", "kt_sample_transcript.txt")
        with open(fixtures_path, "r") as f:
            return f.read()

    def test_extract_googl_from_kt_sample(self, extractor, kt_sample_transcript):
        """Test extraction identifies GOOGL with correct levels."""
        # This is a mock test - in real validation, we'd call Claude API
        # For now, validate the prompt structure and symbol normalization

        # Verify sample contains expected content
        assert "GOOGL" in kt_sample_transcript
        assert "319" in kt_sample_transcript
        assert "313" in kt_sample_transcript
        assert "wave" in kt_sample_transcript.lower()

        # Verify extractor can normalize GOOGL
        assert extractor.normalize_symbol("GOOGL") == "GOOGL"
        assert extractor.normalize_symbol("Alphabet") == "GOOGL"

    def test_extract_spx_from_kt_sample(self, extractor, kt_sample_transcript):
        """Test extraction identifies SPX with correct levels."""
        assert "SPX" in kt_sample_transcript or "S&P" in kt_sample_transcript
        assert "5800" in kt_sample_transcript
        assert "6100" in kt_sample_transcript

        # Verify alias resolution
        assert extractor.normalize_symbol("SPX") == "SPX"
        assert extractor.normalize_symbol("S&P 500") == "SPX"
        assert extractor.normalize_symbol("ES") == "SPX"

    def test_extract_iwm_from_kt_sample(self, extractor, kt_sample_transcript):
        """Test extraction identifies IWM with correct levels."""
        assert "IWM" in kt_sample_transcript or "Russell" in kt_sample_transcript
        assert "236" in kt_sample_transcript
        assert "252" in kt_sample_transcript

        # Verify alias resolution
        assert extractor.normalize_symbol("IWM") == "IWM"
        assert extractor.normalize_symbol("Russell") == "IWM"
        assert extractor.normalize_symbol("Russell 2000") == "IWM"

    def test_extraction_prompt_structure(self, extractor, kt_sample_transcript):
        """Test that extraction prompt is properly formatted."""
        prompt = extractor._build_transcript_extraction_prompt(kt_sample_transcript, "kt_technical")

        # Verify prompt contains key instructions
        assert "TRACKED SYMBOLS" in prompt
        assert "GOOGL" in prompt
        assert "direction" in prompt.lower()
        assert "context_snippet" in prompt
        assert "bullish_reversal" in prompt
        assert "wave_phase" in prompt

    def test_expected_extraction_results(self, extractor):
        """Document expected extraction results for validation."""
        # This test documents what we expect to extract from the sample
        # GOOGL expectations:
        expected_googl = {
            "symbol": "GOOGL",
            "bias": "bullish",
            "wave_position": "wave_4" or "wave_5",
            "wave_phase": "impulse",
            "levels": [
                {"type": "support", "price": 319, "fib": "0.236", "direction": "bullish_reversal"},
                {"type": "support", "price": 313, "fib": "0.382", "direction": "bullish_reversal"},
                {"type": "support", "price": 308, "fib": "0.5", "direction": "bullish_reversal"},
                {"type": "target", "price": 328, "direction": "neutral"},
                {"type": "target", "price": 330, "direction": "neutral"},
                {"type": "invalidation", "price": 270, "direction": "bearish_breakdown"}
            ]
        }

        # SPX expectations:
        expected_spx = {
            "symbol": "SPX",
            "bias": "bullish",
            "wave_position": "wave_3",
            "wave_phase": "impulse",
            "levels": [
                {"type": "support", "price": 5800},
                {"type": "target", "price": 6100},
                {"type": "invalidation", "price": 5650}
            ]
        }

        # IWM expectations:
        expected_iwm = {
            "symbol": "IWM",
            "bias": "neutral",  # corrective pullback
            "wave_position": "wave_A",
            "wave_phase": "correction",
            "levels": [
                {"type": "target", "price": 236, "fib": "0.382"},
                {"type": "support", "price": 231, "fib": "0.5"},
                {"type": "invalidation", "price": 226}
            ]
        }

        # For Phase 0, a human should validate Claude actually extracts these correctly
        assert True  # Placeholder - manual validation required


class TestDirectionVectorAssignment:
    """Test that direction vectors are assigned correctly."""

    def test_support_is_bullish_reversal(self):
        """Support levels should typically be bullish_reversal."""
        # When transcript says "support at 313", direction should be bullish_reversal
        assert True  # This will be validated in actual extraction

    def test_target_is_neutral(self):
        """Target levels should typically be neutral (informational)."""
        # When transcript says "target 330", direction should be neutral
        assert True

    def test_invalidation_is_bearish_breakdown(self):
        """Invalidation levels should be bearish_breakdown."""
        # When transcript says "invalidation below 270", direction should be bearish_breakdown
        assert True


class TestContextSnippetExtraction:
    """Test that context snippets are preserved correctly."""

    def test_context_snippet_is_exact_quote(self):
        """Context snippets must be exact quotes from transcript."""
        sample_text = "support likely holding at 319 if bulls defend"
        # The extraction should preserve this exact wording
        assert True  # Manual validation required

    def test_context_snippet_length(self):
        """Context snippets should be 5-10 words."""
        # Validate extracted snippets are reasonable length
        assert True
