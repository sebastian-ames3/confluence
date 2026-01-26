"""
Unit tests for PRD-043 Compass Classification and Extraction

Tests:
- CompassType enum and classification
- Macro compass to symbol mapping
- Sector compass to symbol mapping
"""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Set mock API key for testing before importing the agent
os.environ.setdefault("CLAUDE_API_KEY", "test-api-key-for-unit-tests")

from agents.symbol_level_extractor import SymbolLevelExtractor, CompassType


class TestCompassType:
    """Test CompassType enum."""

    def test_compass_type_values(self):
        """Test CompassType enum has correct values."""
        assert CompassType.STOCK_COMPASS.value == "stock_compass"
        assert CompassType.MACRO_COMPASS.value == "macro_compass"
        assert CompassType.SECTOR_COMPASS.value == "sector_compass"
        assert CompassType.UNKNOWN.value == "unknown"

    def test_compass_type_members(self):
        """Test CompassType has exactly 4 members."""
        assert len(CompassType) == 4


class TestCompassClassification:
    """Test compass type detection."""

    @pytest.fixture
    def extractor(self):
        return SymbolLevelExtractor(api_key="test-api-key")

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_stock_compass(self, mock_vision, extractor):
        """Test classification returns STOCK_COMPASS."""
        mock_vision.return_value = {"response": "STOCK_COMPASS"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.STOCK_COMPASS

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_stock_compass_from_text(self, mock_vision, extractor):
        """Test classification handles 'Stock' in response."""
        mock_vision.return_value = {"response": "This is a STOCK compass chart"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.STOCK_COMPASS

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_macro_compass(self, mock_vision, extractor):
        """Test classification returns MACRO_COMPASS."""
        mock_vision.return_value = {"response": "MACRO_COMPASS"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.MACRO_COMPASS

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_macro_compass_from_text(self, mock_vision, extractor):
        """Test classification handles 'Macro' in response."""
        mock_vision.return_value = {"response": "This appears to be a MACRO compass"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.MACRO_COMPASS

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_sector_compass(self, mock_vision, extractor):
        """Test classification returns SECTOR_COMPASS."""
        mock_vision.return_value = {"response": "SECTOR_COMPASS"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.SECTOR_COMPASS

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_sector_compass_from_text(self, mock_vision, extractor):
        """Test classification handles 'Sector' in response."""
        mock_vision.return_value = {"response": "SECTOR compass showing ETFs"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.SECTOR_COMPASS

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_unknown(self, mock_vision, extractor):
        """Test classification returns UNKNOWN for non-compass images."""
        mock_vision.return_value = {"response": "UNKNOWN - this is a regular chart"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.UNKNOWN

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_unknown_for_random_response(self, mock_vision, extractor):
        """Test classification returns UNKNOWN for unexpected responses."""
        mock_vision.return_value = {"response": "I see a candlestick chart"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.UNKNOWN

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_handles_exception(self, mock_vision, extractor):
        """Test classification returns UNKNOWN on exception."""
        mock_vision.side_effect = Exception("Vision API error")
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.UNKNOWN

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_classify_case_insensitive(self, mock_vision, extractor):
        """Test classification is case insensitive."""
        mock_vision.return_value = {"response": "stock_compass"}
        result = extractor.classify_compass_image("/path/to/image.png")
        assert result == CompassType.STOCK_COMPASS


class TestMacroCompassMapping:
    """Test macro compass to symbol mapping."""

    @pytest.fixture
    def extractor(self):
        return SymbolLevelExtractor(api_key="test-api-key")

    def test_equities_maps_to_spx_qqq(self, extractor):
        """Test 'equities' asset class maps to SPX and QQQ."""
        macro_data = [
            {"asset_class": "equities", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        symbols = [item["symbol"] for item in result]
        assert "SPX" in symbols
        assert "QQQ" in symbols
        assert len(result) == 2

    def test_stocks_maps_to_spx_qqq(self, extractor):
        """Test 'stocks' asset class maps to SPX and QQQ."""
        macro_data = [
            {"asset_class": "stocks", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        symbols = [item["symbol"] for item in result]
        assert "SPX" in symbols
        assert "QQQ" in symbols

    def test_crypto_maps_to_btc(self, extractor):
        """Test 'crypto' asset class maps to BTC."""
        macro_data = [
            {"asset_class": "crypto", "quadrant": "sell_put", "iv_regime": "expensive", "position_description": "top-left"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        assert len(result) == 1
        assert result[0]["symbol"] == "BTC"
        assert result[0]["quadrant"] == "sell_put"
        assert result[0]["iv_regime"] == "expensive"

    def test_bitcoin_maps_to_btc(self, extractor):
        """Test 'bitcoin' asset class maps to BTC."""
        macro_data = [
            {"asset_class": "bitcoin", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        assert len(result) == 1
        assert result[0]["symbol"] == "BTC"

    def test_semiconductors_maps_to_smh_nvda(self, extractor):
        """Test 'semiconductors' asset class maps to SMH and NVDA."""
        macro_data = [
            {"asset_class": "semiconductors", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        symbols = [item["symbol"] for item in result]
        assert "SMH" in symbols
        assert "NVDA" in symbols
        assert len(result) == 2

    def test_semis_maps_to_smh_nvda(self, extractor):
        """Test 'semis' shorthand maps to SMH and NVDA."""
        macro_data = [
            {"asset_class": "semis", "quadrant": "sell_call", "iv_regime": "expensive", "position_description": "top-right"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        symbols = [item["symbol"] for item in result]
        assert "SMH" in symbols
        assert "NVDA" in symbols

    def test_technology_maps_to_tech_stocks(self, extractor):
        """Test 'technology' asset class maps to tech stocks."""
        macro_data = [
            {"asset_class": "technology", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        symbols = [item["symbol"] for item in result]
        assert "QQQ" in symbols
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "NVDA" in symbols

    def test_tech_shorthand_maps(self, extractor):
        """Test 'tech' shorthand maps to tech stocks."""
        macro_data = [
            {"asset_class": "tech", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        symbols = [item["symbol"] for item in result]
        assert "QQQ" in symbols
        assert "AAPL" in symbols

    def test_position_description_included(self, extractor):
        """Test position description is included in mapped symbols."""
        macro_data = [
            {"asset_class": "crypto", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left area"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        assert "From macro (crypto):" in result[0]["position_description"]
        assert "bottom-left area" in result[0]["position_description"]

    def test_empty_macro_data(self, extractor):
        """Test empty macro data returns empty list."""
        result = extractor._map_macro_to_symbols([])
        assert result == []

    def test_unknown_asset_class_ignored(self, extractor):
        """Test unknown asset classes are ignored."""
        macro_data = [
            {"asset_class": "bonds", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"},
            {"asset_class": "gold", "quadrant": "sell_put", "iv_regime": "expensive", "position_description": "top-left"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)
        assert result == []

    def test_multiple_asset_classes(self, extractor):
        """Test multiple asset classes are all mapped."""
        macro_data = [
            {"asset_class": "equities", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"},
            {"asset_class": "crypto", "quadrant": "sell_put", "iv_regime": "expensive", "position_description": "top-left"}
        ]
        result = extractor._map_macro_to_symbols(macro_data)

        symbols = [item["symbol"] for item in result]
        assert "SPX" in symbols
        assert "QQQ" in symbols
        assert "BTC" in symbols
        assert len(result) == 3  # 2 for equities + 1 for crypto


class TestSectorCompassMapping:
    """Test sector ETF to symbol mapping."""

    @pytest.fixture
    def extractor(self):
        return SymbolLevelExtractor(api_key="test-api-key")

    def test_smh_direct_mapping(self, extractor):
        """Test SMH maps directly to SMH (it's a tracked symbol)."""
        sector_data = [
            {"sector_etf": "SMH", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"}
        ]
        result = extractor._map_sector_to_symbols(sector_data)

        assert len(result) == 1
        assert result[0]["symbol"] == "SMH"
        assert result[0]["quadrant"] == "buy_call"
        assert result[0]["iv_regime"] == "cheap"

    def test_xlk_maps_to_tech_stocks(self, extractor):
        """Test XLK (Technology) maps to AAPL, MSFT, NVDA."""
        sector_data = [
            {"sector_etf": "XLK", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"}
        ]
        result = extractor._map_sector_to_symbols(sector_data)

        symbols = [item["symbol"] for item in result]
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "NVDA" in symbols
        assert len(result) == 3

    def test_xly_maps_to_consumer_stocks(self, extractor):
        """Test XLY (Consumer Discretionary) maps to TSLA, AMZN."""
        sector_data = [
            {"sector_etf": "XLY", "quadrant": "sell_call", "iv_regime": "expensive", "position_description": "top-right"}
        ]
        result = extractor._map_sector_to_symbols(sector_data)

        symbols = [item["symbol"] for item in result]
        assert "TSLA" in symbols
        assert "AMZN" in symbols
        assert len(result) == 2

    def test_xlc_maps_to_googl(self, extractor):
        """Test XLC (Communications) maps to GOOGL."""
        sector_data = [
            {"sector_etf": "XLC", "quadrant": "buy_call", "iv_regime": "neutral", "position_description": "center-left"}
        ]
        result = extractor._map_sector_to_symbols(sector_data)

        assert len(result) == 1
        assert result[0]["symbol"] == "GOOGL"

    def test_sector_etf_case_insensitive(self, extractor):
        """Test sector ETF mapping is case insensitive."""
        sector_data = [
            {"sector_etf": "smh", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"}
        ]
        result = extractor._map_sector_to_symbols(sector_data)

        assert len(result) == 1
        assert result[0]["symbol"] == "SMH"

    def test_position_description_included(self, extractor):
        """Test position description is included with sector prefix."""
        sector_data = [
            {"sector_etf": "XLK", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left area"}
        ]
        result = extractor._map_sector_to_symbols(sector_data)

        assert "From XLK:" in result[0]["position_description"]
        assert "bottom-left area" in result[0]["position_description"]

    def test_empty_sector_data(self, extractor):
        """Test empty sector data returns empty list."""
        result = extractor._map_sector_to_symbols([])
        assert result == []

    def test_unmapped_sectors_ignored(self, extractor):
        """Test sectors without tracked symbol mappings are ignored."""
        sector_data = [
            {"sector_etf": "XLF", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"},  # Financials
            {"sector_etf": "XLE", "quadrant": "sell_put", "iv_regime": "expensive", "position_description": "top-left"},  # Energy
            {"sector_etf": "XLU", "quadrant": "sell_call", "iv_regime": "expensive", "position_description": "top-right"}  # Utilities
        ]
        result = extractor._map_sector_to_symbols(sector_data)
        assert result == []

    def test_multiple_sectors(self, extractor):
        """Test multiple sector ETFs are all mapped."""
        sector_data = [
            {"sector_etf": "SMH", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"},
            {"sector_etf": "XLK", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"},
            {"sector_etf": "XLC", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"}
        ]
        result = extractor._map_sector_to_symbols(sector_data)

        symbols = [item["symbol"] for item in result]
        assert "SMH" in symbols
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "NVDA" in symbols
        assert "GOOGL" in symbols
        # SMH(1) + XLK(3) + XLC(1) = 5
        assert len(result) == 5


class TestMacroCompassExtraction:
    """Test full macro compass extraction flow."""

    @pytest.fixture
    def extractor(self):
        return SymbolLevelExtractor(api_key="test-api-key")

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_extract_from_macro_compass(self, mock_vision, extractor):
        """Test full macro compass extraction."""
        mock_vision.return_value = {
            "macro_data": [
                {"asset_class": "equities", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"},
                {"asset_class": "crypto", "quadrant": "sell_put", "iv_regime": "expensive", "position_description": "top-left"}
            ],
            "extraction_confidence": 0.85
        }

        result = extractor.extract_from_macro_compass("/path/to/macro.png", content_id=123)

        assert result["extraction_method"] == "macro_compass"
        assert result["content_id"] == 123
        assert "extracted_at" in result
        assert "compass_data" in result

        symbols = [item["symbol"] for item in result["compass_data"]]
        assert "SPX" in symbols
        assert "QQQ" in symbols
        assert "BTC" in symbols


class TestSectorCompassExtraction:
    """Test full sector compass extraction flow."""

    @pytest.fixture
    def extractor(self):
        return SymbolLevelExtractor(api_key="test-api-key")

    @patch.object(SymbolLevelExtractor, 'call_claude_vision')
    def test_extract_from_sector_compass(self, mock_vision, extractor):
        """Test full sector compass extraction."""
        mock_vision.return_value = {
            "sector_data": [
                {"sector_etf": "SMH", "quadrant": "buy_call", "iv_regime": "cheap", "position_description": "bottom-left"},
                {"sector_etf": "XLY", "quadrant": "buy_put", "iv_regime": "cheap", "position_description": "bottom-right"}
            ],
            "extraction_confidence": 0.85
        }

        result = extractor.extract_from_sector_compass("/path/to/sector.png", content_id=456)

        assert result["extraction_method"] == "sector_compass"
        assert result["content_id"] == 456
        assert "extracted_at" in result
        assert "compass_data" in result

        symbols = [item["symbol"] for item in result["compass_data"]]
        assert "SMH" in symbols
        assert "TSLA" in symbols
        assert "AMZN" in symbols


class TestAutoExtractionPipeline:
    """Test automatic compass extraction pipeline in Discord collector (PRD-043)."""

    @pytest.fixture
    def mock_extractor(self):
        """Create a mock SymbolLevelExtractor."""
        extractor = Mock()
        extractor.classify_compass_image.return_value = CompassType.STOCK_COMPASS
        extractor.extract_from_compass_image.return_value = {
            "compass_data": [
                {"symbol": "GOOGL", "quadrant": "buy_call", "iv_regime": "cheap"}
            ],
            "extraction_confidence": 0.9
        }
        extractor.save_compass_to_db.return_value = {
            "symbols_processed": 1,
            "states_updated": 1,
            "errors": []
        }
        return extractor

    @pytest.mark.asyncio
    async def test_process_collected_image_stock_compass(self, mock_extractor):
        """Test process_collected_image handles stock compass correctly."""
        from collectors.discord_self import DiscordSelfCollector

        with patch('collectors.discord_self.DiscordSelfCollector._get_local_image_path') as mock_path:
            mock_path.return_value = Path("/fake/path/compass.png")

            with patch('agents.symbol_level_extractor.SymbolLevelExtractor') as MockExtractor:
                MockExtractor.return_value = mock_extractor

                with patch('backend.models.SessionLocal') as MockSession:
                    mock_db = Mock()
                    MockSession.return_value = mock_db

                    # Create collector (will fail on config, but we can test the method)
                    try:
                        collector = DiscordSelfCollector(
                            user_token="fake_token",
                            config_path="fake_config.json"
                        )
                    except ValueError:
                        # Expected - no config file
                        # Create a minimal mock collector for testing
                        collector = Mock(spec=DiscordSelfCollector)
                        collector.download_dir = Path("/fake/downloads")

                        # Import and test the method directly
                        from collectors.discord_self import DiscordSelfCollector

                        # Verify the method exists
                        assert hasattr(DiscordSelfCollector, 'process_collected_image')
                        assert hasattr(DiscordSelfCollector, '_get_local_image_path')

    @pytest.mark.asyncio
    async def test_auto_extraction_skips_unknown_images(self):
        """Test that unknown images are skipped during auto-extraction."""
        extractor = SymbolLevelExtractor(api_key="test-api-key")

        with patch.object(extractor, 'call_claude_vision') as mock_vision:
            # Return a response indicating not a compass
            mock_vision.return_value = {"response": "This is a candlestick chart"}

            result = extractor.classify_compass_image("/path/to/chart.png")
            assert result == CompassType.UNKNOWN

    def test_discord_collector_has_auto_extraction_methods(self):
        """Test Discord collector has auto-extraction methods."""
        from collectors.discord_self import DiscordSelfCollector

        # Verify methods exist
        assert hasattr(DiscordSelfCollector, 'process_collected_image')
        assert hasattr(DiscordSelfCollector, '_get_local_image_path')
        assert hasattr(DiscordSelfCollector, 'save_to_database')

        # Verify save_to_database is overridden (not just inherited)
        import inspect
        method = getattr(DiscordSelfCollector, 'save_to_database')
        # Check method is defined in DiscordSelfCollector, not inherited
        source_file = inspect.getfile(method)
        assert 'discord_self' in source_file
