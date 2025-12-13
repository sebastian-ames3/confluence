"""
Unit Tests for PRD-039: Symbol-Level Confluence Tracking

Tests for:
- SymbolLevelExtractor agent
- Symbol alias normalization
- Database models
"""

import pytest
from agents.symbol_level_extractor import SymbolLevelExtractor
from backend.models import SymbolLevel, SymbolState


class TestSymbolLevelExtractor:
    """Tests for the SymbolLevelExtractor agent."""

    def test_normalize_symbol(self):
        """Test symbol aliasing works correctly."""
        extractor = SymbolLevelExtractor()

        # Test canonical symbols
        assert extractor.normalize_symbol("GOOGL") == "GOOGL"
        assert extractor.normalize_symbol("SPX") == "SPX"

        # Test aliases
        assert extractor.normalize_symbol("GOOGLE") == "GOOGL"
        assert extractor.normalize_symbol("google") == "GOOGL"
        assert extractor.normalize_symbol("S&P") == "SPX"
        assert extractor.normalize_symbol("s&p 500") == "SPX"
        assert extractor.normalize_symbol("NASDAQ") == "QQQ"
        assert extractor.normalize_symbol("Russell") == "IWM"
        assert extractor.normalize_symbol("BITCOIN") == "BTC"

        # Test untracked symbols
        assert extractor.normalize_symbol("ORCL") is None
        assert extractor.normalize_symbol("IBM") is None

    def test_tracked_symbols_list(self):
        """Test that all tracked symbols are defined."""
        extractor = SymbolLevelExtractor()

        expected = ['SPX', 'QQQ', 'IWM', 'BTC', 'SMH', 'TSLA', 'NVDA', 'GOOGL', 'AAPL', 'MSFT', 'AMZN']
        assert extractor.TRACKED_SYMBOLS == expected
        assert len(extractor.TRACKED_SYMBOLS) == 11


class TestDatabaseModels:
    """Tests for database models."""

    def test_symbol_level_model(self):
        """Test SymbolLevel model can be instantiated."""
        level = SymbolLevel(
            symbol="GOOGL",
            source="kt_technical",
            level_type="support",
            price=313.04,
            direction="bullish_reversal"
        )
        assert level.symbol == "GOOGL"
        assert level.source == "kt_technical"
        assert level.level_type == "support"
        assert level.price == 313.04
        assert level.direction == "bullish_reversal"

    def test_symbol_state_model(self):
        """Test SymbolState model can be instantiated."""
        state = SymbolState(
            symbol="GOOGL",
            kt_bias="bullish",
            discord_quadrant="buy_call",
            confluence_score=0.92
        )
        assert state.symbol == "GOOGL"
        assert state.kt_bias == "bullish"
        assert state.discord_quadrant == "buy_call"
        assert state.confluence_score == 0.92
