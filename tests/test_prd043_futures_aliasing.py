"""
Unit tests for PRD-043 Futures Symbol Aliasing

Tests the extended symbol normalization that handles:
- Futures notation with slash prefix (/ES, /NQ, /RTY)
- Yahoo Finance notation (ES=F, NQ=F)
- Micro futures (/MES, /MNQ, /M2K)
"""

import os
import pytest

# Set mock API key for testing before importing the agent
os.environ.setdefault("CLAUDE_API_KEY", "test-api-key-for-unit-tests")

from agents.symbol_level_extractor import SymbolLevelExtractor


class TestFuturesAliasing:
    """Test futures notation normalization."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance for testing."""
        return SymbolLevelExtractor(api_key="test-api-key")

    # ==========================================
    # Slash-prefixed futures tests
    # ==========================================

    def test_es_futures_to_spx(self, extractor):
        """Test /ES maps to SPX."""
        assert extractor.normalize_symbol("/ES") == "SPX"

    def test_sp_futures_to_spx(self, extractor):
        """Test /SP maps to SPX."""
        assert extractor.normalize_symbol("/SP") == "SPX"

    def test_nq_futures_to_qqq(self, extractor):
        """Test /NQ maps to QQQ."""
        assert extractor.normalize_symbol("/NQ") == "QQQ"

    def test_rty_futures_to_iwm(self, extractor):
        """Test /RTY maps to IWM."""
        assert extractor.normalize_symbol("/RTY") == "IWM"

    def test_rut_futures_to_iwm(self, extractor):
        """Test /RUT maps to IWM."""
        assert extractor.normalize_symbol("/RUT") == "IWM"

    def test_btc_futures(self, extractor):
        """Test /BTC and /BTCUSD map to BTC."""
        assert extractor.normalize_symbol("/BTC") == "BTC"
        assert extractor.normalize_symbol("/BTCUSD") == "BTC"

    # ==========================================
    # Yahoo Finance / TradingView notation tests
    # ==========================================

    def test_es_f_notation(self, extractor):
        """Test ES=F and ES_F map to SPX."""
        assert extractor.normalize_symbol("ES=F") == "SPX"
        assert extractor.normalize_symbol("ES_F") == "SPX"

    def test_nq_f_notation(self, extractor):
        """Test NQ=F and NQ_F map to QQQ."""
        assert extractor.normalize_symbol("NQ=F") == "QQQ"
        assert extractor.normalize_symbol("NQ_F") == "QQQ"

    def test_rty_f_notation(self, extractor):
        """Test RTY=F and RTY_F map to IWM."""
        assert extractor.normalize_symbol("RTY=F") == "IWM"
        assert extractor.normalize_symbol("RTY_F") == "IWM"

    # ==========================================
    # Micro futures tests
    # ==========================================

    def test_micro_es_futures(self, extractor):
        """Test /MES and MES variations map to SPX."""
        assert extractor.normalize_symbol("/MES") == "SPX"
        assert extractor.normalize_symbol("MES") == "SPX"
        assert extractor.normalize_symbol("MES=F") == "SPX"

    def test_micro_nq_futures(self, extractor):
        """Test /MNQ and MNQ variations map to QQQ."""
        assert extractor.normalize_symbol("/MNQ") == "QQQ"
        assert extractor.normalize_symbol("MNQ") == "QQQ"
        assert extractor.normalize_symbol("MNQ=F") == "QQQ"

    def test_micro_russell_futures(self, extractor):
        """Test /M2K and M2K variations map to IWM."""
        assert extractor.normalize_symbol("/M2K") == "IWM"
        assert extractor.normalize_symbol("M2K") == "IWM"
        assert extractor.normalize_symbol("M2K=F") == "IWM"

    # ==========================================
    # Case insensitivity tests
    # ==========================================

    def test_case_insensitive_futures(self, extractor):
        """Test futures notation is case insensitive."""
        assert extractor.normalize_symbol("/es") == "SPX"
        assert extractor.normalize_symbol("/Es") == "SPX"
        assert extractor.normalize_symbol("/Nq") == "QQQ"
        assert extractor.normalize_symbol("es=f") == "SPX"
        assert extractor.normalize_symbol("Es=F") == "SPX"

    def test_case_insensitive_micro(self, extractor):
        """Test micro futures are case insensitive."""
        assert extractor.normalize_symbol("/mes") == "SPX"
        assert extractor.normalize_symbol("/Mes") == "SPX"
        assert extractor.normalize_symbol("mes=f") == "SPX"

    # ==========================================
    # Whitespace handling tests
    # ==========================================

    def test_whitespace_handling(self, extractor):
        """Test whitespace is properly stripped."""
        assert extractor.normalize_symbol("  /ES  ") == "SPX"
        assert extractor.normalize_symbol("\t/NQ\n") == "QQQ"
        assert extractor.normalize_symbol(" ES=F ") == "SPX"
        assert extractor.normalize_symbol("  GOOGL  ") == "GOOGL"

    # ==========================================
    # Edge cases and error handling
    # ==========================================

    def test_empty_input(self, extractor):
        """Test empty and None inputs return None."""
        assert extractor.normalize_symbol("") is None
        assert extractor.normalize_symbol(None) is None

    def test_whitespace_only_input(self, extractor):
        """Test whitespace-only input returns None."""
        assert extractor.normalize_symbol("   ") is None
        assert extractor.normalize_symbol("\t\n") is None

    def test_unknown_futures(self, extractor):
        """Test unknown futures symbols return None."""
        assert extractor.normalize_symbol("/GC") is None  # Gold futures
        assert extractor.normalize_symbol("/CL") is None  # Crude oil futures
        assert extractor.normalize_symbol("/ZB") is None  # Bond futures
        assert extractor.normalize_symbol("/6E") is None  # Euro futures

    def test_unknown_symbols(self, extractor):
        """Test unknown regular symbols return None."""
        assert extractor.normalize_symbol("XYZ") is None
        assert extractor.normalize_symbol("UNKNOWN") is None
        assert extractor.normalize_symbol("FAKE") is None

    # ==========================================
    # Existing aliases still work
    # ==========================================

    def test_existing_index_aliases(self, extractor):
        """Test existing index aliases still work."""
        assert extractor.normalize_symbol("SPY") == "SPX"
        assert extractor.normalize_symbol("S&P") == "SPX"
        assert extractor.normalize_symbol("S&P 500") == "SPX"
        assert extractor.normalize_symbol("ES") == "SPX"  # Without slash

    def test_existing_nasdaq_aliases(self, extractor):
        """Test existing Nasdaq aliases still work."""
        assert extractor.normalize_symbol("NASDAQ") == "QQQ"
        assert extractor.normalize_symbol("NASDAQ 100") == "QQQ"
        assert extractor.normalize_symbol("NDX") == "QQQ"
        assert extractor.normalize_symbol("NQ") == "QQQ"  # Without slash

    def test_existing_russell_aliases(self, extractor):
        """Test existing Russell aliases still work."""
        assert extractor.normalize_symbol("RUSSELL") == "IWM"
        assert extractor.normalize_symbol("RUSSELL 2000") == "IWM"
        assert extractor.normalize_symbol("RTY") == "IWM"  # Without slash
        assert extractor.normalize_symbol("RUT") == "IWM"

    def test_existing_company_aliases(self, extractor):
        """Test existing company name aliases still work."""
        assert extractor.normalize_symbol("Google") == "GOOGL"
        assert extractor.normalize_symbol("GOOGLE") == "GOOGL"
        assert extractor.normalize_symbol("ALPHABET") == "GOOGL"
        assert extractor.normalize_symbol("Apple") == "AAPL"
        assert extractor.normalize_symbol("NVIDIA") == "NVDA"
        assert extractor.normalize_symbol("TESLA") == "TSLA"
        assert extractor.normalize_symbol("AMAZON") == "AMZN"
        assert extractor.normalize_symbol("MICROSOFT") == "MSFT"

    def test_existing_crypto_aliases(self, extractor):
        """Test existing crypto aliases still work."""
        assert extractor.normalize_symbol("BITCOIN") == "BTC"
        assert extractor.normalize_symbol("BTCUSD") == "BTC"

    def test_existing_semi_aliases(self, extractor):
        """Test existing semiconductor aliases still work."""
        assert extractor.normalize_symbol("SEMIS") == "SMH"
        assert extractor.normalize_symbol("SEMICONDUCTORS") == "SMH"

    # ==========================================
    # Canonical symbols unchanged
    # ==========================================

    def test_canonical_symbols_unchanged(self, extractor):
        """Test canonical symbols pass through unchanged."""
        for symbol in ['SPX', 'QQQ', 'IWM', 'BTC', 'SMH', 'TSLA', 'NVDA', 'GOOGL', 'AAPL', 'MSFT', 'AMZN']:
            assert extractor.normalize_symbol(symbol) == symbol

    def test_canonical_symbols_lowercase(self, extractor):
        """Test lowercase canonical symbols are normalized to uppercase."""
        assert extractor.normalize_symbol("spx") == "SPX"
        assert extractor.normalize_symbol("qqq") == "QQQ"
        assert extractor.normalize_symbol("googl") == "GOOGL"


class TestFuturesInExtraction:
    """Test that futures symbols are correctly normalized during extraction."""

    @pytest.fixture
    def extractor(self):
        return SymbolLevelExtractor(api_key="test-api-key")

    def test_validate_extraction_normalizes_futures(self, extractor):
        """Test _validate_extraction normalizes futures symbols."""
        raw_result = {
            "symbols": [
                {"symbol": "/ES", "bias": "bullish", "levels": []},
                {"symbol": "GOOGL", "bias": "neutral", "levels": []},
            ],
            "extraction_confidence": 0.9
        }

        validated = extractor._validate_extraction(raw_result, content_id=123, method="transcript")

        symbols = [s["symbol"] for s in validated["symbols"]]
        assert "SPX" in symbols
        assert "GOOGL" in symbols
        assert "/ES" not in symbols

    def test_validate_extraction_filters_unknown(self, extractor):
        """Test _validate_extraction filters out unknown symbols."""
        raw_result = {
            "symbols": [
                {"symbol": "/ES", "bias": "bullish", "levels": []},
                {"symbol": "/GC", "bias": "bullish", "levels": []},  # Gold - not tracked
                {"symbol": "FAKE", "bias": "neutral", "levels": []},  # Unknown
            ],
            "extraction_confidence": 0.9
        }

        validated = extractor._validate_extraction(raw_result, content_id=123, method="transcript")

        symbols = [s["symbol"] for s in validated["symbols"]]
        assert len(symbols) == 1
        assert "SPX" in symbols
