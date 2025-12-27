"""
Image Intelligence Agent

Interprets charts, graphs, and volatility surfaces using Claude Vision API.
Handles technical charts, volatility surfaces, and positioning charts from Discord and KT Technical.

Priority Chart Types:
- Volatility surfaces (IV vs spot, term structure)
- Technical price charts (support/resistance, Elliott Wave)
- Positioning charts (options flow, dealer positioning)
"""

import os
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ImageIntelligenceAgent(BaseAgent):
    """
    Agent for analyzing charts and images using Claude Vision API.

    Pipeline:
    1. Load image file
    2. Convert to base64
    3. Analyze with Claude Vision API
    4. Extract structured insights
    """

    # Chart type keywords for detection
    CHART_TYPE_KEYWORDS = {
        "volatility_surface": [
            "iv", "implied volatility", "vol surface", "skew", "term structure",
            "vix", "volatility", "vega", "theta"
        ],
        "technical_chart": [
            "price", "chart", "candlestick", "support", "resistance",
            "elliott wave", "fibonacci", "moving average", "trend"
        ],
        "positioning_chart": [
            "positioning", "flow", "open interest", "dealer", "gamma",
            "options flow", "put call", "sentiment"
        ]
    }

    # Supported image formats
    SUPPORTED_FORMATS = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif"
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250514"
    ):
        """
        Initialize Image Intelligence Agent.

        Args:
            api_key: Claude API key (defaults to env var)
            model: Claude model to use (must support vision)
        """
        super().__init__(api_key=api_key, model=model)
        logger.info(f"Initialized ImageIntelligenceAgent")

    def analyze(
        self,
        image_path: str,
        source: str = "unknown",
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Full pipeline: image → Claude Vision → structured insights.

        Args:
            image_path: Path to image file
            source: Source of image (discord, kt_technical, twitter)
            context: Optional context about the image (e.g., "SPX volatility update")
            metadata: Optional metadata

        Returns:
            Complete analysis with chart interpretation
        """
        if metadata is None:
            metadata = {}

        try:
            logger.info(f"Analyzing image: {image_path}")
            logger.info(f"Source: {source}, Context: {context}")

            # Step 1: Load and encode image
            image_data, media_type = self._load_image(image_path)

            # Step 2: Detect chart type (preliminary)
            chart_type = self._detect_chart_type(context, metadata)

            # Step 3: Analyze with Claude Vision
            analysis = self.analyze_image(
                image_data=image_data,
                media_type=media_type,
                source=source,
                chart_type=chart_type,
                context=context,
                metadata=metadata
            )

            # Add metadata
            analysis["image_path"] = image_path
            analysis["source"] = source
            analysis["context"] = context or "No context provided"
            analysis["processed_at"] = datetime.utcnow().isoformat()

            logger.info(
                f"Analysis complete. Chart type: {analysis.get('image_type', 'unknown')}, "
                f"Tickers: {analysis.get('tickers', [])}"
            )

            return analysis

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise

    def _load_image(self, image_path: str) -> tuple:
        """
        Load image file and convert to base64.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (base64_data, media_type)
        """
        try:
            path = Path(image_path)

            if not path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            # Check format
            extension = path.suffix.lower()
            if extension not in self.SUPPORTED_FORMATS:
                raise ValueError(
                    f"Unsupported image format: {extension}. "
                    f"Supported: {list(self.SUPPORTED_FORMATS.keys())}"
                )

            media_type = self.SUPPORTED_FORMATS[extension]

            # Read and encode
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            image_base64 = base64.standard_b64encode(image_bytes).decode('utf-8')

            logger.info(
                f"Loaded image: {path.name} ({len(image_bytes)} bytes, {media_type})"
            )

            return image_base64, media_type

        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            raise

    def _detect_chart_type(
        self,
        context: Optional[str],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Preliminary chart type detection from context/metadata.

        Args:
            context: Context string
            metadata: Metadata dict

        Returns:
            Preliminary chart type
        """
        # Check metadata first
        if "chart_type" in metadata:
            return metadata["chart_type"]

        # Check context string
        if context:
            context_lower = context.lower()
            for chart_type, keywords in self.CHART_TYPE_KEYWORDS.items():
                if any(keyword in context_lower for keyword in keywords):
                    logger.info(f"Detected chart type from context: {chart_type}")
                    return chart_type

        return "unknown"

    def analyze_image(
        self,
        image_data: str,
        media_type: str,
        source: str,
        chart_type: str,
        context: Optional[str],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze image with Claude Vision API.

        Args:
            image_data: Base64 encoded image
            media_type: MIME type (image/png, image/jpeg, etc.)
            source: Source of image
            chart_type: Preliminary chart type
            context: Optional context
            metadata: Metadata

        Returns:
            Structured analysis
        """
        try:
            logger.info(f"Analyzing image with Claude Vision (type: {chart_type})")

            # Build system prompt based on source and chart type
            system_prompt = self._get_system_prompt(source, chart_type)

            # Build user prompt
            user_prompt = self._build_analysis_prompt(source, chart_type, context, metadata)

            # Call Claude Vision API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.0,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": user_prompt
                            }
                        ]
                    }
                ]
            )

            # Extract and parse response
            response_text = response.content[0].text
            analysis = self._parse_json_response(response_text)

            # Validate response
            required_fields = [
                "image_type",
                "interpretation",
                "tickers"
            ]
            self.validate_response_schema(analysis, required_fields)

            logger.info(
                f"Vision analysis complete: {analysis.get('image_type', 'unknown')}, "
                f"{len(analysis.get('tickers', []))} tickers identified"
            )

            return analysis

        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            raise

    def _get_system_prompt(self, source: str, chart_type: str) -> str:
        """
        Get system prompt based on source and chart type.

        Args:
            source: Source of image
            chart_type: Chart type

        Returns:
            System prompt for Claude
        """
        if source == "discord":
            if chart_type == "volatility_surface":
                return """You are analyzing a volatility surface or options-related chart from Options Insight (Discord).

These charts typically show implied volatility metrics, term structure, skew, or options positioning.

Focus on:
- Implied volatility levels (30d, 60d, 90d IV)
- Term structure shape (contango, backwardation, inversion)
- Skew (put vs call IV)
- Key levels and inflection points
- Options flow and positioning (dealer gamma, open interest)
- What this means for market direction and risk

Extract specific numbers, strikes, expirations, and actionable insights."""

            elif chart_type == "positioning_chart":
                return """You are analyzing an options positioning or flow chart from Options Insight (Discord).

These charts show dealer positioning, gamma exposure, put/call ratios, or sentiment indicators.

Focus on:
- Dealer positioning (long gamma, short gamma, key strikes)
- Options flow direction (heavy call/put buying)
- Open interest concentrations
- Sentiment indicators
- Implications for price action and volatility

Be specific about strikes, expirations, and positioning levels."""

        elif source == "kt_technical":
            return """You are analyzing a technical price chart from KT Technical Analysis.

These are professional-grade technical analysis charts with Elliott Wave counts, Fibonacci levels,
support/resistance zones, and trend analysis.

Focus on:
- Current Elliott Wave count and position in wave structure
- Key support and resistance levels with specific price points
- Fibonacci retracement/extension levels
- Trend direction and strength
- Entry/exit zones and stop loss levels
- Target prices
- What the technical setup suggests for near-term price action

Be precise with price levels and technical labels."""

        # Default prompt for unknown types
        return """You are analyzing a financial market chart or graph.

Identify what type of chart this is and extract key insights:
- Chart type (price chart, volatility surface, positioning, etc.)
- Key levels, prices, or metrics shown
- Tickers or assets referenced
- Main insight or signal
- Bullish, bearish, or neutral interpretation

Be specific and extract quantitative data where visible."""

    def _build_analysis_prompt(
        self,
        source: str,
        chart_type: str,
        context: Optional[str],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Build analysis prompt for Claude Vision.

        Args:
            source: Source
            chart_type: Chart type
            context: Context
            metadata: Metadata

        Returns:
            User prompt
        """
        context_text = f"Context: {context}" if context else "No context provided"

        prompt = f"""Analyze this financial chart image.

**Source**: {source}
**Preliminary Chart Type**: {chart_type}
**{context_text}**

Extract the following information in JSON format:

{{
    "image_type": "volatility_surface|technical_chart|positioning_chart|price_chart|other",
    "extracted_text": ["any visible text, labels, or annotations"],
    "interpretation": {{
        "main_insight": "primary takeaway from this chart",
        "key_levels": ["specific price levels, IV levels, or key data points"],
        "technical_details": "detailed analysis of what the chart shows",
        "implied_volatility": {{"30d": null, "60d": null, "90d": null}} OR null if not applicable,
        "support_resistance": {{"support": [], "resistance": []}} OR null if not applicable,
        "trend": "bullish|bearish|neutral|ranging|unknown",
        "positioning": "any options positioning or flow info visible" OR null
    }},
    "tickers": ["list of tickers/assets shown in chart"],
    "sentiment": "bullish|bearish|neutral|mixed",
    "conviction": <0-10 integer based on clarity of signal>,
    "time_horizon": "intraday|1w|1m|3m|6m|unknown",
    "actionable_levels": ["specific prices, strikes, or levels for trading"],
    "falsification_criteria": ["what would invalidate this setup/view"]
}}

Instructions:
- Be VERY specific with numbers - extract exact prices, IV levels, percentages
- For technical charts: identify support/resistance, trends, wave counts
- For volatility charts: extract IV levels, skew, term structure shape
- For positioning charts: identify gamma levels, flow direction, strikes
- If text in image is hard to read, note this in extracted_text
- Conviction: rate 0-10 based on clarity of setup and signal strength
- Only include tickers if they are explicitly shown or clearly implied

Return ONLY valid JSON, no markdown formatting."""

        return prompt

    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        Get basic image information without full analysis.

        Args:
            image_path: Path to image

        Returns:
            Image metadata
        """
        try:
            path = Path(image_path)

            if not path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            file_size = path.stat().st_size
            extension = path.suffix.lower()

            return {
                "file_name": path.name,
                "file_path": str(path),
                "file_size_bytes": file_size,
                "file_size_kb": round(file_size / 1024, 2),
                "format": extension,
                "media_type": self.SUPPORTED_FORMATS.get(extension, "unknown")
            }

        except Exception as e:
            logger.error(f"Failed to get image info: {e}")
            raise
