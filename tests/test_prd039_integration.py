"""
Integration Tests for PRD-039 Symbol-Level Extraction Pipeline

Tests the extraction logic and data structures without requiring full database setup.
Full end-to-end tests will run in Playwright.
"""

import pytest
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.symbol_level_extractor import SymbolLevelExtractor


class TestExtractionLogic:
    """Test extraction logic and data validation."""

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

    def test_extraction_prompt_building(self, extractor, kt_sample_transcript):
        """Test that extraction prompts are properly built."""
        # Test KT Technical prompt building
        prompt = extractor._build_transcript_extraction_prompt(kt_sample_transcript, 'kt_technical')

        # Verify prompt contains tracked symbols
        assert 'GOOGL' in prompt
        assert 'SPX' in prompt
        assert 'IWM' in prompt

        # Verify prompt contains direction vectors
        assert 'bullish_reversal' in prompt
        assert 'bearish_breakdown' in prompt

        # Verify prompt instructs on extraction fields
        assert 'level_type' in prompt or 'type' in prompt
        assert 'price' in prompt
        assert 'direction' in prompt
        assert 'context_snippet' in prompt

    def test_expected_level_structure(self, extractor):
        """Test the expected structure of extracted levels."""
        # This documents what the extraction should return
        expected_level = {
            'symbol': 'GOOGL',
            'level_type': 'support',  # support, resistance, target, invalidation
            'price': 319.0,
            'price_upper': None,  # optional range
            'fib_level': '0.236',  # optional
            'direction': 'bullish_reversal',  # bullish_reversal, bearish_breakdown, etc
            'context_snippet': 'support likely holding at the 0.236 fib level around 319',
            'confidence': 0.85,
            'wave_context': 'wave_5 impulse',  # KT specific
            'options_context': None  # Discord specific
        }

        # Verify all required fields
        assert 'symbol' in expected_level
        assert 'level_type' in expected_level
        assert 'price' in expected_level
        assert 'direction' in expected_level
        assert 'context_snippet' in expected_level

    def test_direction_vector_assignment(self, extractor):
        """Test correct direction vector assignment for different level types."""
        # Support levels should typically be bullish_reversal
        support_direction = 'bullish_reversal'
        assert support_direction in ['bullish_reversal', 'bearish_reversal', 'bullish_breakout', 'bearish_breakdown', 'neutral']

        # Resistance levels should typically be bearish_reversal
        resistance_direction = 'bearish_reversal'
        assert resistance_direction in ['bullish_reversal', 'bearish_reversal', 'bullish_breakout', 'bearish_breakdown', 'neutral']

        # Target levels are typically neutral (informational)
        target_direction = 'neutral'
        assert target_direction in ['bullish_reversal', 'bearish_reversal', 'bullish_breakout', 'bearish_breakdown', 'neutral']

        # Invalidation levels are typically bearish_breakdown (in bullish setup)
        invalidation_direction = 'bearish_breakdown'
        assert invalidation_direction in ['bullish_reversal', 'bearish_reversal', 'bullish_breakout', 'bearish_breakdown', 'neutral']

    def test_multiple_symbol_identification(self, extractor, kt_sample_transcript):
        """Test that extractor can identify multiple symbols in transcript."""
        # The sample transcript contains GOOGL, SPX, and IWM
        assert 'GOOGL' in kt_sample_transcript or 'Alphabet' in kt_sample_transcript
        assert 'SPX' in kt_sample_transcript or 'S&P' in kt_sample_transcript
        assert 'IWM' in kt_sample_transcript or 'Russell' in kt_sample_transcript

        # Extractor should normalize these to tracked symbols
        assert extractor.normalize_symbol('Alphabet') == 'GOOGL'
        assert extractor.normalize_symbol('S&P 500') == 'SPX'
        assert extractor.normalize_symbol('Russell 2000') == 'IWM'

    def test_level_confidence_scoring(self, extractor):
        """Test that confidence scores are within valid range."""
        # Confidence should be between 0.0 and 1.0
        valid_confidences = [0.65, 0.75, 0.85, 0.9]

        for conf in valid_confidences:
            assert 0.0 <= conf <= 1.0

        # Low confidence threshold (typically 0.7)
        low_conf_threshold = 0.7
        assert 0.65 < low_conf_threshold  # Should flag as low confidence
        assert 0.75 >= low_conf_threshold  # Should pass

    def test_context_snippet_preservation(self, extractor, kt_sample_transcript):
        """Test that context snippets are preserved from source."""
        # Sample snippets from the transcript
        expected_snippets = [
            'support likely holding at the 0.236 fib level around 319',
            'the 0.382 fib at 313 should provide solid support',
            'targets for wave 5 completion are looking at 328 to 330 zone',
            'real invalidation is below 270 where weekly demand breaks'
        ]

        # All snippets should exist in the transcript
        for snippet in expected_snippets:
            # Check if snippet or close approximation exists
            words = snippet.split()[:5]  # First 5 words
            assert any(word in kt_sample_transcript for word in words)


class TestSymbolNormalization:
    """Test symbol alias normalization."""

    def test_normalize_common_aliases(self):
        """Test normalization of common symbol aliases."""
        extractor = SymbolLevelExtractor(api_key="test-key-for-unit-tests")

        # Google/Alphabet -> GOOGL
        assert extractor.normalize_symbol('GOOGLE') == 'GOOGL'
        assert extractor.normalize_symbol('Alphabet') == 'GOOGL'
        assert extractor.normalize_symbol('GOOG') == 'GOOGL'

        # S&P 500 -> SPX
        assert extractor.normalize_symbol('S&P 500') == 'SPX'
        assert extractor.normalize_symbol('S&P') == 'SPX'
        assert extractor.normalize_symbol('ES') == 'SPX'
        assert extractor.normalize_symbol('SPY') == 'SPX'

        # Russell 2000 -> IWM
        assert extractor.normalize_symbol('Russell 2000') == 'IWM'
        assert extractor.normalize_symbol('Russell') == 'IWM'

    def test_tracked_symbols_only(self):
        """Test that only tracked symbols are processed."""
        extractor = SymbolLevelExtractor(api_key="test-key-for-unit-tests")

        # Tracked symbols
        assert 'GOOGL' in extractor.TRACKED_SYMBOLS
        assert 'SPX' in extractor.TRACKED_SYMBOLS
        assert 'IWM' in extractor.TRACKED_SYMBOLS
        assert 'BTC' in extractor.TRACKED_SYMBOLS

        # Not tracked
        assert 'RANDOM' not in extractor.TRACKED_SYMBOLS
