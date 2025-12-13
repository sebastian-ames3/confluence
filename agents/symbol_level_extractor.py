"""
Symbol Level Extractor Agent (PRD-039)

Extracts symbol-specific price levels from multiple sources:
- KT Technical transcripts (Elliott Wave analysis)
- KT Technical chart images (annotated levels)
- Discord text posts (options analysis, gamma levels)
- Discord Stock Compass images (quadrant positioning)
"""

import os
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.base_agent import BaseAgent
from backend.utils.sanitization import sanitize_content_text, truncate_for_prompt

logger = logging.getLogger(__name__)


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

        Args:
            symbol_text: Raw symbol text (e.g., "Google", "S&P", "GOOGL")

        Returns:
            Canonical ticker or None if not tracked
        """
        symbol_upper = symbol_text.strip().upper()

        # Check if already canonical
        if symbol_upper in self.TRACKED_SYMBOLS:
            return symbol_upper

        # Check aliases
        return self.SYMBOL_ALIASES.get(symbol_upper)

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
                max_tokens=4096,
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

            # Call Claude vision (this would use the vision API)
            # For now, this is a placeholder - vision API integration needed
            result = {
                "symbols": [],
                "extraction_confidence": 0.0
            }

            logger.warning("Chart vision extraction not yet implemented - placeholder")
            return result

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

            # Placeholder for vision API
            result = {
                "compass_data": [],
                "extraction_confidence": 0.0
            }

            logger.warning("Compass vision extraction not yet implemented - placeholder")
            return result

        except Exception as e:
            logger.error(f"Compass vision extraction failed: {e}")
            raise

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

Only include symbols from: SPX, QQQ, IWM, BTC, SMH, TSLA, NVDA, GOOGL, AAPL, MSFT, AMZN"""

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
