"""
Symbol Level Extractor Agent (PRD-039, PRD-043)

Extracts symbol-specific price levels from multiple sources:
- KT Technical transcripts (Elliott Wave analysis)
- KT Technical chart images (annotated levels)
- Discord text posts (options analysis, gamma levels)
- Discord Stock Compass images (quadrant positioning)
- Discord Macro Compass images (asset class positioning) [PRD-043]
- Discord Sector Compass images (sector ETF positioning) [PRD-043]
"""

import os
import logging
import re
from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from agents.base_agent import BaseAgent
from backend.utils.sanitization import sanitize_content_text, truncate_for_prompt

logger = logging.getLogger(__name__)


class CompassType(Enum):
    """Types of compass images from Discord (PRD-043)."""
    STOCK_COMPASS = "stock_compass"      # Individual stocks in quadrants
    MACRO_COMPASS = "macro_compass"      # Asset classes (equities, bonds, gold)
    SECTOR_COMPASS = "sector_compass"    # Sector ETFs (XLK, XLF, SMH, etc.)
    UNKNOWN = "unknown"


class SymbolLevelExtractor(BaseAgent):
    """
    Extracts price levels and wave counts for tracked symbols.

    Handles:
    - Text parsing from transcripts and Discord posts
    - Image parsing from charts and compass diagrams
    - Symbol aliasing (GOOGLE -> GOOGL, S&P -> SPX, etc.)
    - Direction vector assignment
    - Context snippet extraction
    """

    # The 11 tracked symbols
    TRACKED_SYMBOLS = ['SPX', 'QQQ', 'IWM', 'BTC', 'SMH', 'TSLA', 'NVDA', 'GOOGL', 'AAPL', 'MSFT', 'AMZN']

    # Comprehensive symbol aliasing - normalize all variations to canonical tickers
    SYMBOL_ALIASES = {
        # GOOGL variations
        'GOOGLE': 'GOOGL', 'GOOG': 'GOOGL', 'ALPHABET': 'GOOGL',
        # AAPL variations
        'APPLE': 'AAPL',
        # AMZN variations
        'AMAZON': 'AMZN',
        # MSFT variations
        'MICROSOFT': 'MSFT',
        # TSLA variations
        'TESLA': 'TSLA',
        # NVDA variations
        'NVIDIA': 'NVDA',
        # IWM variations
        'RUSSELL': 'IWM', 'RUSSELL 2000': 'IWM', 'RTY': 'IWM', 'RUT': 'IWM',
        # QQQ variations
        'NASDAQ': 'QQQ', 'NASDAQ 100': 'QQQ', 'NQ': 'QQQ', 'NDX': 'QQQ', 'QS': 'QQQ',
        # SPX variations
        'S&P': 'SPX', 'S&P 500': 'SPX', 'SP500': 'SPX', 'ES': 'SPX', 'SPY': 'SPX',
        # BTC variations
        'BITCOIN': 'BTC', 'BTCUSD': 'BTC',
        # SMH variations
        'SEMIS': 'SMH', 'SEMICONDUCTORS': 'SMH',

        # PRD-043: Futures notation (with slash prefix)
        '/ES': 'SPX', '/SP': 'SPX',
        '/NQ': 'QQQ',
        '/RTY': 'IWM', '/RUT': 'IWM',
        '/BTC': 'BTC', '/BTCUSD': 'BTC',

        # PRD-043: Yahoo Finance / TradingView futures notation
        'ES=F': 'SPX', 'ES_F': 'SPX',
        'NQ=F': 'QQQ', 'NQ_F': 'QQQ',
        'RTY=F': 'IWM', 'RTY_F': 'IWM',

        # PRD-043: Micro futures
        '/MES': 'SPX', '/MNQ': 'QQQ', '/M2K': 'IWM',
        'MES': 'SPX', 'MNQ': 'QQQ', 'M2K': 'IWM',
        'MES=F': 'SPX', 'MNQ=F': 'QQQ', 'M2K=F': 'IWM',
    }

    # Transcript chunking: Long videos (30+ min) must be split to avoid "lost in middle" errors
    CHUNK_SIZE_MINUTES = 5  # Split transcripts every 5 minutes or by speaker change

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """Initialize the SymbolLevelExtractor agent."""
        super().__init__(api_key=api_key, model=model)
        logger.info(f"Initialized SymbolLevelExtractor")

    def normalize_symbol(self, symbol_text: str) -> Optional[str]:
        """
        Normalize symbol variations to canonical ticker.

        Handles:
        - Standard tickers (GOOGL, AAPL)
        - Company names (Google, Apple)
        - Futures notation (/ES, /NQ, ES=F) [PRD-043]
        - Index names (S&P 500, Nasdaq 100)

        Args:
            symbol_text: Raw symbol text (e.g., "Google", "S&P", "GOOGL", "/ES")

        Returns:
            Canonical ticker or None if not tracked
        """
        if not symbol_text:
            return None

        symbol_clean = symbol_text.strip().upper()

        # Check if already canonical
        if symbol_clean in self.TRACKED_SYMBOLS:
            return symbol_clean

        # Check aliases (includes /ES, ES=F, etc.)
        if symbol_clean in self.SYMBOL_ALIASES:
            return self.SYMBOL_ALIASES[symbol_clean]

        # PRD-043: Try stripping leading slash and check again
        if symbol_clean.startswith('/'):
            without_slash = symbol_clean[1:]
            if without_slash in self.TRACKED_SYMBOLS:
                return without_slash
            if without_slash in self.SYMBOL_ALIASES:
                return self.SYMBOL_ALIASES[without_slash]

        return None

    def extract_from_transcript(
        self,
        transcript: str,
        source: str,
        content_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract price levels from KT Technical or Discord transcript.

        Args:
            transcript: Full transcript text
            source: 'kt_technical' or 'discord'
            content_id: ID of raw_content this came from

        Returns:
            Extraction results with symbols and levels
        """
        try:
            logger.info(f"Extracting levels from {source} transcript (content_id={content_id})")

            # Sanitize and truncate for prompt
            safe_transcript = sanitize_content_text(transcript)
            truncated = truncate_for_prompt(safe_transcript, max_chars=15000)

            # Build extraction prompt
            prompt = self._build_transcript_extraction_prompt(truncated, source)

            # Call Claude
            result = self.call_claude(
                prompt=prompt,
                system_prompt=self._get_transcript_extraction_system_prompt(),
                max_tokens=16384,
                temperature=0.0,
                expect_json=True
            )

            # Validate and normalize
            validated = self._validate_extraction(result, content_id, 'transcript')

            logger.info(f"Extracted {len(validated.get('symbols', []))} symbols with levels")
            return validated

        except Exception as e:
            logger.error(f"Transcript extraction failed: {e}")
            raise

    def extract_from_chart_image(
        self,
        image_path: str,
        content_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract price levels from KT Technical annotated chart using Claude vision.

        Args:
            image_path: Path to chart image file
            content_id: ID of raw_content this came from

        Returns:
            Extraction results with symbols and levels
        """
        try:
            logger.info(f"Extracting levels from chart image: {image_path}")

            # Build vision prompt
            prompt = self._get_chart_vision_prompt()
            system_prompt = self._get_chart_vision_system_prompt()

            # Call Claude vision API
            result = self.call_claude_vision(
                prompt=prompt,
                image_path=image_path,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.0,
                expect_json=True
            )

            # Validate and normalize
            validated = self._validate_extraction(result, content_id, 'chart_image')

            logger.info(f"Extracted {len(validated.get('symbols', []))} symbols from chart image")
            return validated

        except FileNotFoundError as e:
            logger.error(f"Chart image not found: {e}")
            return {"symbols": [], "extraction_confidence": 0.0, "error": str(e)}
        except Exception as e:
            logger.error(f"Chart vision extraction failed: {e}")
            raise

    def extract_from_compass_image(
        self,
        image_path: str,
        content_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract quadrant positions from Discord Stock Compass using Claude vision.

        Args:
            image_path: Path to compass image file
            content_id: ID of raw_content this came from

        Returns:
            Compass data with symbol positions
        """
        try:
            logger.info(f"Extracting from Stock Compass: {image_path}")

            # Build vision prompt
            prompt = self._get_compass_vision_prompt()
            system_prompt = self._get_compass_vision_system_prompt()

            # Call Claude vision API
            result = self.call_claude_vision(
                prompt=prompt,
                image_path=image_path,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.0,
                expect_json=True
            )

            # Add metadata
            result["content_id"] = content_id
            result["extraction_method"] = "compass_image"
            result["extracted_at"] = datetime.utcnow().isoformat()

            # Filter to only tracked symbols
            if "compass_data" in result:
                filtered_data = []
                for item in result["compass_data"]:
                    symbol = item.get("symbol", "")
                    canonical = self.normalize_symbol(symbol)
                    if canonical:
                        item["symbol"] = canonical
                        filtered_data.append(item)
                result["compass_data"] = filtered_data

            logger.info(f"Extracted {len(result.get('compass_data', []))} symbols from compass image")
            return result

        except FileNotFoundError as e:
            logger.error(f"Compass image not found: {e}")
            return {"compass_data": [], "extraction_confidence": 0.0, "error": str(e)}
        except Exception as e:
            logger.error(f"Compass vision extraction failed: {e}")
            raise

    def classify_compass_image(self, image_path: str) -> CompassType:
        """
        Classify compass image type before extraction (PRD-043).

        Uses Claude vision to determine if image is:
        - Stock Compass (individual stocks)
        - Macro Compass (asset classes)
        - Sector Compass (sector ETFs)
        - Unknown (not a compass chart)

        Args:
            image_path: Path to image file

        Returns:
            CompassType enum value
        """
        try:
            logger.info(f"Classifying compass image: {image_path}")

            prompt = """Classify this image. Is it a:
1. STOCK_COMPASS - Shows individual stock tickers (AAPL, GOOGL, TSLA, etc.) positioned in quadrants
2. MACRO_COMPASS - Shows asset classes (Equities, Bonds, Gold, Oil, Crypto, etc.) positioned in quadrants
3. SECTOR_COMPASS - Shows sector ETFs (XLK, XLF, XLE, SMH, XLY, etc.) positioned in quadrants
4. UNKNOWN - Not a compass/quadrant chart, or cannot determine type

Look for:
- Stock Compass: Individual company tickers like AAPL, MSFT, GOOGL, NVDA
- Macro Compass: Asset class labels like "Equities", "Bonds", "Commodities", "Crypto"
- Sector Compass: Sector ETF tickers like XLK, XLF, XLE, SMH, XLY, XLC

Return ONLY one of: STOCK_COMPASS, MACRO_COMPASS, SECTOR_COMPASS, UNKNOWN"""

            result = self.call_claude_vision(
                prompt=prompt,
                image_path=image_path,
                system_prompt="You are classifying financial chart images. Respond with only the classification type.",
                max_tokens=50,
                temperature=0.0
            )

            # Parse response
            response_text = str(result) if not isinstance(result, dict) else result.get("response", str(result))
            response_upper = response_text.upper().strip()

            if "STOCK" in response_upper:
                logger.info(f"Classified as STOCK_COMPASS")
                return CompassType.STOCK_COMPASS
            elif "MACRO" in response_upper:
                logger.info(f"Classified as MACRO_COMPASS")
                return CompassType.MACRO_COMPASS
            elif "SECTOR" in response_upper:
                logger.info(f"Classified as SECTOR_COMPASS")
                return CompassType.SECTOR_COMPASS

            logger.info(f"Classified as UNKNOWN")
            return CompassType.UNKNOWN

        except Exception as e:
            logger.error(f"Compass classification failed: {e}")
            return CompassType.UNKNOWN

    def extract_from_macro_compass(
        self,
        image_path: str,
        content_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract asset class positioning from Macro Compass (PRD-043).

        Maps relevant asset classes to tracked symbols:
        - "Equities" positioning informs SPX/QQQ bias
        - "Crypto" positioning informs BTC
        - "Semiconductors" informs SMH/NVDA

        Args:
            image_path: Path to macro compass image
            content_id: ID of raw_content this came from

        Returns:
            Compass data with symbol positions mapped from asset classes
        """
        try:
            logger.info(f"Extracting from Macro Compass: {image_path}")

            prompt = """Analyze this Macro Compass image showing asset class positioning.

The compass has 4 quadrants based on:
- Y-axis: Implied Volatility (high=top, low=bottom)
- X-axis: Directional bias (bullish=left, bearish=right)

Quadrants:
- Top-left: SELL PUT (bullish, high IV)
- Top-right: SELL CALL (bearish, high IV)
- Bottom-left: BUY CALL (bullish, low IV)
- Bottom-right: BUY PUT (bearish, low IV)

Identify the position of these asset classes:
- Equities / Stocks
- Crypto / Bitcoin
- Semiconductors / Semis / Chips
- Technology / Tech

For each asset class found, return:
{
  "macro_data": [
    {
      "asset_class": "equities",
      "quadrant": "buy_call",
      "iv_regime": "cheap",
      "position_description": "bottom-left, bullish with low IV"
    },
    {
      "asset_class": "crypto",
      "quadrant": "sell_put",
      "iv_regime": "expensive",
      "position_description": "top-left, bullish with high IV"
    }
  ],
  "extraction_confidence": 0.85
}

Return ONLY valid JSON, no markdown formatting."""

            system_prompt = """You are an expert at reading Macro Compass diagrams showing asset class positioning.

The Macro Compass is a 2x2 quadrant chart:
- Y-axis: Implied Volatility (high=top, low=bottom)
- X-axis: Directional bias (bullish=left, bearish=right)

Your job is to identify which asset classes appear and their quadrant positions.
Focus on: Equities, Crypto, Semiconductors, Technology.

You must respond with valid JSON only."""

            result = self.call_claude_vision(
                prompt=prompt,
                image_path=image_path,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.0,
                expect_json=True
            )

            # Add metadata
            result["content_id"] = content_id
            result["extraction_method"] = "macro_compass"
            result["extracted_at"] = datetime.utcnow().isoformat()

            # Map asset classes to tracked symbols
            result["compass_data"] = self._map_macro_to_symbols(result.get("macro_data", []))

            logger.info(f"Extracted {len(result.get('compass_data', []))} symbols from macro compass")
            return result

        except FileNotFoundError as e:
            logger.error(f"Macro compass image not found: {e}")
            return {"compass_data": [], "macro_data": [], "extraction_confidence": 0.0, "error": str(e)}
        except Exception as e:
            logger.error(f"Macro compass extraction failed: {e}")
            raise

    def extract_from_sector_compass(
        self,
        image_path: str,
        content_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Extract sector ETF positioning from Sector Compass (PRD-043).

        Maps relevant sectors to tracked symbols:
        - SMH (Semiconductors) - directly tracked
        - XLK (Technology) - informs AAPL, MSFT, GOOGL, NVDA
        - XLY (Consumer Discretionary) - informs TSLA, AMZN
        - XLC (Communications) - informs GOOGL

        Args:
            image_path: Path to sector compass image
            content_id: ID of raw_content this came from

        Returns:
            Compass data with symbol positions mapped from sectors
        """
        try:
            logger.info(f"Extracting from Sector Compass: {image_path}")

            prompt = """Analyze this Sector Compass image showing sector ETF positioning.

The compass has 4 quadrants:
- Top-left: SELL PUT (bullish, high IV)
- Top-right: SELL CALL (bearish, high IV)
- Bottom-left: BUY CALL (bullish, low IV)
- Bottom-right: BUY PUT (bearish, low IV)

Look for these sector ETFs and their positions:
- SMH (Semiconductors) - IMPORTANT: directly tracked
- XLK (Technology)
- XLY (Consumer Discretionary)
- XLC (Communications)
- XLF (Financials)
- XLE (Energy)
- XLI (Industrials)
- XLV (Healthcare)
- XLP (Consumer Staples)
- XLU (Utilities)
- XLRE (Real Estate)
- XLB (Materials)

Return:
{
  "sector_data": [
    {
      "sector_etf": "SMH",
      "quadrant": "buy_call",
      "iv_regime": "cheap",
      "position_description": "bottom-left area, bullish with low IV"
    },
    {
      "sector_etf": "XLK",
      "quadrant": "buy_call",
      "iv_regime": "cheap",
      "position_description": "bottom-left area"
    }
  ],
  "extraction_confidence": 0.85
}

Return ONLY valid JSON, no markdown formatting."""

            system_prompt = """You are an expert at reading Sector Compass diagrams showing sector ETF positioning.

The Sector Compass is a 2x2 quadrant chart:
- Y-axis: Implied Volatility (high=top, low=bottom)
- X-axis: Directional bias (bullish=left, bearish=right)

Your job is to identify which sector ETFs appear and their quadrant positions.
Pay special attention to: SMH, XLK, XLY, XLC as these map to tracked stocks.

You must respond with valid JSON only."""

            result = self.call_claude_vision(
                prompt=prompt,
                image_path=image_path,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.0,
                expect_json=True
            )

            # Add metadata
            result["content_id"] = content_id
            result["extraction_method"] = "sector_compass"
            result["extracted_at"] = datetime.utcnow().isoformat()

            # Map sectors to tracked symbols
            result["compass_data"] = self._map_sector_to_symbols(result.get("sector_data", []))

            logger.info(f"Extracted {len(result.get('compass_data', []))} symbols from sector compass")
            return result

        except FileNotFoundError as e:
            logger.error(f"Sector compass image not found: {e}")
            return {"compass_data": [], "sector_data": [], "extraction_confidence": 0.0, "error": str(e)}
        except Exception as e:
            logger.error(f"Sector compass extraction failed: {e}")
            raise

    def _map_macro_to_symbols(self, macro_data: List[Dict]) -> List[Dict]:
        """
        Map macro asset class data to tracked symbols (PRD-043).

        Args:
            macro_data: List of asset class positions from macro compass

        Returns:
            List of symbol positions derived from asset classes
        """
        symbol_data = []

        for item in macro_data:
            asset_class = item.get("asset_class", "").lower()
            quadrant = item.get("quadrant")
            iv_regime = item.get("iv_regime")
            position_desc = item.get("position_description", "")

            # Map asset classes to symbols
            if asset_class in ["equities", "stocks", "equity"]:
                # Apply to both SPX and QQQ
                for symbol in ["SPX", "QQQ"]:
                    symbol_data.append({
                        "symbol": symbol,
                        "quadrant": quadrant,
                        "iv_regime": iv_regime,
                        "position_description": f"From macro ({asset_class}): {position_desc}"
                    })
            elif asset_class in ["crypto", "bitcoin", "btc", "cryptocurrency"]:
                symbol_data.append({
                    "symbol": "BTC",
                    "quadrant": quadrant,
                    "iv_regime": iv_regime,
                    "position_description": f"From macro ({asset_class}): {position_desc}"
                })
            elif asset_class in ["semiconductors", "semis", "chips", "semiconductor"]:
                for symbol in ["SMH", "NVDA"]:
                    symbol_data.append({
                        "symbol": symbol,
                        "quadrant": quadrant,
                        "iv_regime": iv_regime,
                        "position_description": f"From macro ({asset_class}): {position_desc}"
                    })
            elif asset_class in ["technology", "tech"]:
                for symbol in ["QQQ", "AAPL", "MSFT", "NVDA"]:
                    symbol_data.append({
                        "symbol": symbol,
                        "quadrant": quadrant,
                        "iv_regime": iv_regime,
                        "position_description": f"From macro ({asset_class}): {position_desc}"
                    })

        return symbol_data

    def _map_sector_to_symbols(self, sector_data: List[Dict]) -> List[Dict]:
        """
        Map sector ETF data to tracked symbols (PRD-043).

        Args:
            sector_data: List of sector ETF positions from sector compass

        Returns:
            List of symbol positions derived from sector ETFs
        """
        symbol_data = []

        # Sector to symbol mapping
        sector_symbol_map = {
            "SMH": ["SMH"],  # Direct match - semiconductors
            "XLK": ["AAPL", "MSFT", "NVDA"],  # Technology sector
            "XLY": ["TSLA", "AMZN"],  # Consumer discretionary
            "XLC": ["GOOGL"],  # Communications
        }

        for item in sector_data:
            sector_etf = item.get("sector_etf", "").upper()
            quadrant = item.get("quadrant")
            iv_regime = item.get("iv_regime")
            position_desc = item.get("position_description", "")

            if sector_etf in sector_symbol_map:
                for symbol in sector_symbol_map[sector_etf]:
                    symbol_data.append({
                        "symbol": symbol,
                        "quadrant": quadrant,
                        "iv_regime": iv_regime,
                        "position_description": f"From {sector_etf}: {position_desc}"
                    })

        return symbol_data

    def _get_transcript_extraction_system_prompt(self) -> str:
        """System prompt for transcript extraction."""
        return """You are extracting price levels for specific symbols from investment research content.

Your job is to identify mentions of tracked symbols and extract specific price levels with context.

Be rigorous:
- Only extract levels you are confident about (>70% confidence)
- Context snippets must be EXACT quotes from the transcript
- If a number is ambiguous or you're unsure which symbol it refers to, skip it

You must respond with valid JSON only."""

    def _build_transcript_extraction_prompt(self, transcript: str, source: str) -> str:
        """
        Build the extraction prompt for transcripts.

        Args:
            transcript: Sanitized transcript text
            source: Source type

        Returns:
            Formatted prompt
        """
        return f"""Extract price levels for specific symbols from this investment research content.

TRACKED SYMBOLS: SPX, QQQ, IWM, BTC, SMH, TSLA, NVDA, GOOGL, AAPL, MSFT, AMZN
(Also match aliases: "Google"=GOOGL, "Nasdaq"=QQQ, "S&P"=SPX, "Russell"=IWM, etc.)

For each tracked symbol mentioned, extract:
1. Support levels (with fib level if mentioned, e.g., "0.382")
2. Resistance levels
3. Target prices (with wave context if Elliott Wave, e.g., "wave 5 target")
4. Invalidation levels (the specific price where the thesis breaks)
5. Wave position (if Elliott Wave: wave_1 through wave_5, direction up/down)
6. Wave phase: Is this an IMPULSE (trending, 5-wave move) or CORRECTION (choppy, 3-wave move)?
7. Overall bias (bullish/bearish/neutral)

For each level, you MUST also extract:
- direction: How should this level be traded?
  - bullish_reversal: Buy at support, expecting bounce up
  - bearish_reversal: Sell at resistance, expecting rejection down
  - bullish_breakout: Buy above this level on breakout
  - bearish_breakdown: Sell below this level on breakdown
  - neutral: Level is informational only
- context_snippet: The exact 5-10 words surrounding this level in the transcript
- invalidation_price: At what price does THIS LEVEL become invalid? (e.g., "support at 313 invalid if we lose 308")

**Content to analyze:**
<content>
{transcript}
</content>

Return JSON in this format:
{{
  "symbols": [
    {{
      "symbol": "GOOGL",
      "bias": "bullish",
      "wave_position": "wave_4",
      "wave_direction": "up",
      "wave_phase": "impulse",
      "levels": [
        {{
          "type": "support",
          "price": 313.04,
          "fib": "0.382",
          "direction": "bullish_reversal",
          "context": "wave iv retracement",
          "context_snippet": "support likely holding at 313 if bulls defend",
          "invalidation_price": 308.27
        }},
        {{
          "type": "target",
          "price": 330,
          "direction": "neutral",
          "context": "wave 5 completion",
          "context_snippet": "looking for wave 5 to complete around 328 to 330",
          "invalidation_price": null
        }}
      ],
      "notes": "Monster breakout from 270 low, looking for wave 5 to 328-330 if 310 support holds"
    }}
  ],
  "extraction_confidence": 0.9
}}

Return ONLY valid JSON, no markdown formatting."""

    def _get_chart_vision_prompt(self) -> str:
        """Prompt for chart image vision analysis."""
        return """Analyze this trading chart image and extract all annotated price levels.

Look for:
1. Fibonacci retracement/extension levels (labeled like "0.382 (313.04)")
2. Wave labels ((i), (ii), (iii), (iv), (v) or 1, 2, 3, 4, 5)
3. Support/resistance zones (horizontal lines or boxes)
4. Target projections (arrows pointing to price levels)
5. Invalidation levels (often marked in red or labeled "hard invalidation")
6. Text annotations explaining the setup
7. "BOS" (Break of Structure) markers
8. Demand/supply zones (often shown as shaded rectangles)

Identify the symbol from the chart title/ticker shown (bottom-left corner typically).

Determine the wave phase:
- IMPULSE: 5-wave trending structure (waves labeled 1-2-3-4-5 or i-ii-iii-iv-v)
- CORRECTION: 3-wave counter-trend structure (waves labeled A-B-C)

For each level, determine the direction vector:
- Support zones with bullish projection arrows = bullish_reversal
- Resistance zones with bearish projection arrows = bearish_reversal
- Levels with "if breaks above" annotations = bullish_breakout
- Levels with "if loses" or "hard invalidation" = bearish_breakdown

Return JSON with same schema as transcript extraction, including:
- wave_phase (impulse/correction)
- direction for each level
- context_snippet (use the text annotation near the level if visible)"""

    def _get_compass_vision_prompt(self) -> str:
        """Prompt for Stock Compass vision analysis."""
        return """Analyze this Options Insight Stock Compass image.

The compass has 4 quadrants:
- Top-left: SELL PUT (bullish, high IV)
- Top-right: SELL CALL (bearish, high IV)
- Bottom-left: BUY CALL (bullish, low IV)
- Bottom-right: BUY PUT (bearish, low IV)
- Center: neutral/spread strategies

Y-axis: Implied Volatility (high at top, low at bottom)
X-axis: Directional bias (bullish left, bearish right)

Tickers are color-coded by sector:
- Green: Technology
- Blue: Communications
- Yellow: Consumer Cyclical
- Light Green: Consumer Non-Cyclical
- Gray: Industrial
- Red: Financial

For each ticker you can identify, return:
{{
  "compass_data": [
    {{
      "symbol": "GOOGL",
      "quadrant": "buy_call",
      "iv_regime": "cheap",
      "position_description": "bottom-left area, suggesting bullish with low IV"
    }}
  ],
  "extraction_confidence": 0.85
}}

Only include symbols from: SPX, QQQ, IWM, BTC, SMH, TSLA, NVDA, GOOGL, AAPL, MSFT, AMZN

Return ONLY valid JSON, no markdown formatting."""

    def _get_chart_vision_system_prompt(self) -> str:
        """System prompt for chart vision analysis."""
        return """You are an expert technical analyst extracting price levels from annotated trading charts.

Your job is to:
1. Identify the symbol from chart title or ticker
2. Extract all annotated price levels (fib levels, support, resistance, targets)
3. Determine wave structure (impulse vs correction)
4. Assign direction vectors to each level

Be rigorous:
- Only extract levels that are clearly visible and labeled
- Context snippets should use visible text annotations
- If you cannot identify the symbol, set extraction_confidence to 0.0

You must respond with valid JSON only."""

    def _get_compass_vision_system_prompt(self) -> str:
        """System prompt for compass vision analysis."""
        return """You are an expert at reading Options Insight Stock Compass diagrams.

The Stock Compass is a 2x2 quadrant chart:
- Y-axis: Implied Volatility (high=top, low=bottom)
- X-axis: Directional bias (bullish=left, bearish=right)

Quadrants:
- Top-left: SELL PUT (bullish, high IV) - sell premium into high vol
- Top-right: SELL CALL (bearish, high IV) - sell premium into high vol
- Bottom-left: BUY CALL (bullish, low IV) - long directional with cheap vol
- Bottom-right: BUY PUT (bearish, low IV) - long directional with cheap vol
- Center: Neutral/spread strategies

Your job is to identify which tracked symbols appear and which quadrant they're in.
Only include symbols from: SPX, QQQ, IWM, BTC, SMH, TSLA, NVDA, GOOGL, AAPL, MSFT, AMZN

You must respond with valid JSON only."""

    def _validate_extraction(
        self,
        result: Dict[str, Any],
        content_id: Optional[int],
        method: str
    ) -> Dict[str, Any]:
        """
        Validate and normalize extraction results.

        Args:
            result: Raw extraction from Claude
            content_id: Source content ID
            method: Extraction method

        Returns:
            Validated and normalized result
        """
        # Ensure structure
        if "symbols" not in result:
            result["symbols"] = []

        # Normalize symbols and add metadata
        normalized_symbols = []
        for sym_data in result.get("symbols", []):
            symbol = sym_data.get("symbol")
            if not symbol:
                continue

            # Normalize symbol
            canonical = self.normalize_symbol(symbol)
            if not canonical:
                logger.warning(f"Symbol {symbol} not in tracked list, skipping")
                continue

            sym_data["symbol"] = canonical
            sym_data["content_id"] = content_id
            sym_data["extraction_method"] = method

            # Add timestamps
            for level in sym_data.get("levels", []):
                level["extracted_at"] = datetime.utcnow().isoformat()

            normalized_symbols.append(sym_data)

        result["symbols"] = normalized_symbols
        result["extracted_at"] = datetime.utcnow().isoformat()

        return result

    def save_extraction_to_db(
        self,
        db: Session,
        extraction_result: Dict[str, Any],
        source: str,
        content_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Save extraction results to database.

        Creates SymbolLevel records for each level and updates SymbolState
        for each symbol. Calculates confluence scores after saving.

        Args:
            db: Database session
            extraction_result: Result from extract_from_transcript or vision methods
            source: Source type ('kt_technical' or 'discord')
            content_id: ID of raw_content this came from

        Returns:
            Summary of saved records
        """
        from backend.models import SymbolLevel, SymbolState
        from backend.utils.staleness_manager import update_symbol_confluence

        summary = {
            "symbols_processed": 0,
            "levels_created": 0,
            "states_updated": 0,
            "errors": []
        }

        try:
            symbols_data = extraction_result.get("symbols", [])

            for sym_data in symbols_data:
                symbol = sym_data.get("symbol")
                if not symbol:
                    continue

                try:
                    # Get or create SymbolState
                    state = db.query(SymbolState).filter_by(symbol=symbol).first()
                    if not state:
                        state = SymbolState(symbol=symbol)
                        db.add(state)
                        db.flush()

                    # Update state based on source
                    now = datetime.utcnow()

                    if source == 'kt_technical':
                        state.kt_wave_position = sym_data.get("wave_position")
                        state.kt_wave_direction = sym_data.get("wave_direction")
                        state.kt_wave_phase = sym_data.get("wave_phase")
                        state.kt_bias = sym_data.get("bias")
                        state.kt_notes = sym_data.get("notes")
                        state.kt_last_updated = now
                        state.kt_is_stale = False
                        state.kt_stale_warning = None
                        state.kt_source_content_id = content_id

                        # Extract primary target/support/invalidation from levels
                        for level in sym_data.get("levels", []):
                            level_type = level.get("type")
                            price = level.get("price")
                            if level_type == "target" and price:
                                state.kt_primary_target = price
                            elif level_type == "support" and price:
                                if not state.kt_primary_support or price > state.kt_primary_support:
                                    state.kt_primary_support = price
                            elif level_type == "invalidation" and price:
                                state.kt_invalidation = price

                    elif source == 'discord':
                        # For Discord text posts with quadrant info
                        if "quadrant" in sym_data:
                            state.discord_quadrant = sym_data.get("quadrant")
                            state.discord_iv_regime = sym_data.get("iv_regime")
                            state.discord_strategy_rec = sym_data.get("strategy_rec")
                        state.discord_notes = sym_data.get("notes")
                        state.discord_last_updated = now
                        state.discord_is_stale = False
                        state.discord_source_content_id = content_id

                    state.updated_at = now
                    summary["states_updated"] += 1

                    # Create SymbolLevel records for each level
                    for level in sym_data.get("levels", []):
                        level_record = SymbolLevel(
                            symbol=symbol,
                            source=source,
                            level_type=level.get("type", "unknown"),
                            price=level.get("price"),
                            price_upper=level.get("price_upper"),
                            significance=level.get("significance"),
                            direction=level.get("direction"),
                            wave_context=level.get("context"),
                            fib_level=level.get("fib"),
                            context_snippet=level.get("context_snippet"),
                            confidence=extraction_result.get("extraction_confidence", 0.8),
                            extracted_from_content_id=content_id,
                            extraction_method=sym_data.get("extraction_method", "transcript"),
                            invalidation_price=level.get("invalidation_price"),
                            is_active=True,
                            is_stale=False
                        )
                        db.add(level_record)
                        summary["levels_created"] += 1

                    summary["symbols_processed"] += 1

                except Exception as e:
                    logger.error(f"Error saving data for {symbol}: {e}")
                    summary["errors"].append(f"{symbol}: {str(e)}")

            # Commit all changes
            db.commit()

            # Update confluence scores for all processed symbols
            for sym_data in symbols_data:
                symbol = sym_data.get("symbol")
                if symbol:
                    try:
                        update_symbol_confluence(db, symbol)
                    except Exception as e:
                        logger.warning(f"Failed to update confluence for {symbol}: {e}")

            logger.info(f"Saved extraction: {summary['symbols_processed']} symbols, "
                       f"{summary['levels_created']} levels, {summary['states_updated']} states updated")

            return summary

        except Exception as e:
            logger.error(f"Failed to save extraction to database: {e}")
            db.rollback()
            summary["errors"].append(str(e))
            return summary

    def save_compass_to_db(
        self,
        db: Session,
        compass_result: Dict[str, Any],
        content_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Save Stock Compass extraction results to database.

        Updates SymbolState with Discord quadrant/IV data.

        Args:
            db: Database session
            compass_result: Result from extract_from_compass_image
            content_id: ID of raw_content this came from

        Returns:
            Summary of saved records
        """
        from backend.models import SymbolState
        from backend.utils.staleness_manager import update_symbol_confluence

        summary = {
            "symbols_processed": 0,
            "states_updated": 0,
            "errors": []
        }

        try:
            compass_data = compass_result.get("compass_data", [])
            now = datetime.utcnow()

            for item in compass_data:
                symbol = item.get("symbol")
                if not symbol:
                    continue

                try:
                    # Get or create SymbolState
                    state = db.query(SymbolState).filter_by(symbol=symbol).first()
                    if not state:
                        state = SymbolState(symbol=symbol)
                        db.add(state)
                        db.flush()

                    # Update Discord state from compass
                    state.discord_quadrant = item.get("quadrant")
                    state.discord_iv_regime = item.get("iv_regime")
                    state.discord_last_updated = now
                    state.discord_is_stale = False
                    state.discord_source_content_id = content_id
                    state.updated_at = now

                    summary["states_updated"] += 1
                    summary["symbols_processed"] += 1

                except Exception as e:
                    logger.error(f"Error saving compass data for {symbol}: {e}")
                    summary["errors"].append(f"{symbol}: {str(e)}")

            # Commit all changes
            db.commit()

            # Update confluence scores
            for item in compass_data:
                symbol = item.get("symbol")
                if symbol:
                    try:
                        update_symbol_confluence(db, symbol)
                    except Exception as e:
                        logger.warning(f"Failed to update confluence for {symbol}: {e}")

            logger.info(f"Saved compass data: {summary['symbols_processed']} symbols updated")

            return summary

        except Exception as e:
            logger.error(f"Failed to save compass data to database: {e}")
            db.rollback()
            summary["errors"].append(str(e))
            return summary
