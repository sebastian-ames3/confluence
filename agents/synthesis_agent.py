"""
Synthesis Agent

Generates human-readable research synthesis from collected content.
Uses an experienced macro analyst persona to naturally weight evidence
and produce concise summaries of investment themes.

This agent replaces the complex confluence scoring UI with natural
language synthesis that Claude generates using internal judgment.

V2 (PRD-020): Enhanced actionable synthesis with specific levels,
quantified conviction, entry/stop/target, and time-horizon bucketing.
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SynthesisAgent(BaseAgent):
    """
    Agent for generating research synthesis from collected content.

    Instead of displaying numeric scores, this agent produces
    1-3 paragraph summaries highlighting:
    - Key macro themes across sources
    - High-conviction ideas where sources align
    - Notable contradictions worth monitoring
    - Significant regime shifts or catalysts
    """

    # System prompt defining the analyst persona
    SYSTEM_PROMPT = """You are an experienced macro analyst synthesizing investment research from multiple premium sources.

You naturally weight evidence based on:
- Source credibility and track record
- Recency of information
- Cross-source confluence (multiple independent sources agreeing)
- Clarity of the investment thesis
- Presence of clear falsification criteria

Your goal is to help a sophisticated investor quickly understand the current research landscape.

When analyzing content, consider:
1. What are the dominant themes emerging across sources?
2. Where do multiple independent sources agree (high conviction)?
3. Where are there notable contradictions or divergences?
4. Are there any regime shifts or catalyst events being discussed?

Be direct and actionable. Avoid hedging language. If sources strongly agree on something, say so clearly.
If there's genuine uncertainty or disagreement, acknowledge it honestly."""

    # Source reliability weights (used in prompts)
    SOURCE_WEIGHTS = {
        "42macro": "high (institutional-grade macro research)",
        "discord": "high (Options Insight - professional options analysis)",
        "youtube": "medium (varies by channel)",
        "substack": "medium (Visser Labs - macro/crypto analysis)",
        "kt_technical": "medium-high (technical analysis focus)"
    }

    # V2: Numeric source weights for conviction calculation
    SOURCE_WEIGHTS_V2 = {
        "42macro": 1.5,      # Darius Dale - institutional-grade
        "discord": 1.5,     # Options Insight - professional options
        "kt_technical": 1.2, # Systematic technical analysis
        "substack": 1.0,    # Visser Labs - macro/crypto
        "youtube": 0.8      # Variable quality
    }

    # V3: Research Consumption Hub (PRD-021)
    # Focused on helping users consume research, NOT generate trade ideas
    SYSTEM_PROMPT_V3 = """You are a research assistant helping a sophisticated investor efficiently consume multiple paid research services.

Your role is to SYNTHESIZE what the sources are saying, NOT to generate trade recommendations.

KEY PRINCIPLES:
1. DESCRIPTIVE, NOT PRESCRIPTIVE: Describe what sources say, don't tell the user what to trade
2. CONFLUENCE IDENTIFICATION: Surface where independent sources align on views/themes
3. CONFLICT SURFACING: Highlight where sources disagree - these are important to monitor
4. ATTENTION PRIORITIZATION: Help the user know where to focus their limited time
5. RE-REVIEW RECOMMENDATIONS: Identify older content that's become MORE relevant due to current conditions

SOURCE CONTEXT:
- Discord (Imran): Tactical options flow, specific trade ideas - the ONLY source that gives trades
- KT Technical: Elliott Wave analysis on ~10 instruments - provides levels that may align with other views
- 42Macro: Institutional macro research - provides backdrop/context, NOT trade ideas
- YouTube channels: Macro commentary - provides backdrop/context, NOT trade ideas
  - Moonshots: AI, technology, and abundance focus (Peter Diamandis podcast with guests)
  - Jordi Visser Labs: Information synthesis, macro perspectives
  - Forward Guidance: Macroeconomics, Fed policy, finance
  - 42 Macro: Institutional macro research (video format)
- Substack: Thematic research - provides backdrop/context, NOT trade ideas

CONFLUENCE MEANS: "Does the macro backdrop (42Macro, YouTube, Substack) support the tactical positioning (Discord)?"
Example: Discord positions for vol expansion → 42Macro highlights liquidity concerns → KT Technical shows support tests → CONFLUENCE

SOURCE WEIGHTS (for determining weighted lean when sources disagree):
- 42Macro: 1.5x (institutional-grade)
- Discord: 1.5x (professional options flow)
- KT Technical: 1.2x (systematic technical)
- Substack: 1.0x (quality macro/crypto)
- YouTube: 0.8x (variable quality)

OUTPUT TONE:
Write like you're briefing a colleague: "Your macro sources are saying X. Discord is positioned for Y. The technical picture shows Z."
Do NOT write like you're giving trading instructions."""

    # V2: Enhanced system prompt for actionable synthesis
    SYSTEM_PROMPT_V2 = """You are a senior macro strategist synthesizing investment research for a professional trading desk.

Your output must be ACTIONABLE, not merely observational. Every idea should include:
- Specific price levels (not "support levels" but "5950-5980 support zone")
- Quantified conviction (count sources agreeing/disagreeing)
- Clear entry, stop, and target levels where available in source material
- Time horizon classification (tactical: <4 weeks, strategic: 1-6 months)

SOURCE WEIGHTING (apply these multipliers when calculating conviction):
- 42Macro (Darius Dale): 1.5x weight - institutional-grade macro research
- Discord Options Insight (Imran): 1.5x weight - professional options flow analysis
- KT Technical: 1.2x weight - systematic technical analysis
- Substack (Visser Labs): 1.0x weight - macro/crypto analysis
- YouTube: 0.8x weight - variable quality, verify with other sources

CONVICTION SCORING:
- Calculate raw score as (agreeing sources / total sources mentioning topic)
- Apply source weights to get weighted score (sum of agreeing weights / sum of all weights)
- High conviction: weighted score >= 0.70
- Medium conviction: weighted score 0.50-0.69
- Low conviction: weighted score < 0.50

LEVEL EXTRACTION:
When sources mention specific levels, strikes, or targets, ALWAYS include them.
If a source says "watching 5950 support" -> include "5950" in your output.
If a source mentions "Dec VIX 16 calls" -> include the specific strike and expiry.
Never use vague language like "key support" without the actual number.

CONTRADICTION RESOLUTION:
When sources disagree, provide a WEIGHTED synthesis view:
"Given 42Macro (1.5x) and Options Insight (1.5x) both bullish vs YouTube (0.8x) bearish,
the weighted view is moderately bullish with [specific invalidation conditions]."

CATALYST EXTRACTION:
Extract SPECIFIC DATES from content. Convert "December FOMC" to "December 17-18 FOMC".
Known 2025 dates: FOMC Dec 17-18, NFP first Friday of month, CPI ~10th of month.
Rate each catalyst's expected impact (high/medium/low) on the relevant thesis.

Be direct. Be specific. Be actionable."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-5-20251101"
    ):
        """
        Initialize Synthesis Agent.

        Args:
            api_key: Claude API key (defaults to env var)
            model: Claude model to use
        """
        super().__init__(api_key=api_key, model=model)
        logger.info("Initialized SynthesisAgent")

    def analyze(
        self,
        content_items: List[Dict[str, Any]],
        time_window: str = "24h",
        focus_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate synthesis from collected content.

        Args:
            content_items: List of analyzed content items to synthesize
            time_window: Time window being analyzed ("24h", "7d", "30d")
            focus_topic: Optional specific topic to focus on

        Returns:
            Synthesis result with structured output
        """
        if not content_items:
            return self._empty_synthesis(time_window)

        # Build the prompt with content summaries
        prompt = self._build_synthesis_prompt(content_items, time_window, focus_topic)

        # Call Claude for synthesis
        response = self.call_claude(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=2000,
            temperature=0.3,  # Slightly creative for natural writing
            expect_json=True
        )

        # Add metadata
        response["time_window"] = time_window
        response["content_count"] = len(content_items)
        response["sources_included"] = list(set(item.get("source", "unknown") for item in content_items))
        response["generated_at"] = datetime.utcnow().isoformat() + "Z"

        # Validate required fields
        required_fields = ["synthesis", "key_themes", "high_conviction_ideas"]
        self.validate_response_schema(response, required_fields)

        logger.info(f"Generated synthesis for {len(content_items)} items over {time_window}")
        return response

    def _build_synthesis_prompt(
        self,
        content_items: List[Dict[str, Any]],
        time_window: str,
        focus_topic: Optional[str] = None
    ) -> str:
        """Build the prompt for synthesis generation."""

        # Group content by source (PRD-040: use channel_display for YouTube)
        by_source = {}
        for item in content_items:
            source = item.get("source", "unknown")
            # PRD-040: Use channel display name for YouTube content
            if source == "youtube" and item.get("channel_display"):
                display_key = f"youtube:{item['channel_display']}"
            else:
                display_key = source
            if display_key not in by_source:
                by_source[display_key] = []
            by_source[display_key].append(item)

        # Build content summary section
        content_section = ""
        for source_key, items in by_source.items():
            # PRD-040: Extract display name and base source for weight lookup
            if source_key.startswith("youtube:"):
                channel_name = source_key.split(":", 1)[1]
                base_source = "youtube"
                reliability = self.SOURCE_WEIGHTS.get(base_source, "medium")
                content_section += f"\n### YOUTUBE - {channel_name} (Reliability: {reliability})\n"
            else:
                reliability = self.SOURCE_WEIGHTS.get(source_key, "medium")
                content_section += f"\n### {source_key.upper()} (Reliability: {reliability})\n"

            for item in items:
                title = item.get("title", "Untitled")
                content_type = item.get("type", "unknown")
                timestamp = item.get("timestamp", "")
                summary = item.get("summary", item.get("content_text", ""))[:500]
                themes = item.get("themes", [])
                sentiment = item.get("sentiment", "")
                tickers = item.get("tickers", [])

                content_section += f"\n**{title}** ({content_type}, {timestamp})\n"
                if themes:
                    content_section += f"Themes: {', '.join(themes)}\n"
                if sentiment:
                    content_section += f"Sentiment: {sentiment}\n"
                if tickers:
                    content_section += f"Tickers: {', '.join(tickers)}\n"
                if summary:
                    content_section += f"Summary: {summary}\n"

        # Build the full prompt
        focus_instruction = ""
        if focus_topic:
            focus_instruction = f"\n\nFOCUS: Pay particular attention to content related to: {focus_topic}\n"

        prompt = f"""Analyze the following research content collected over the past {time_window} and generate a synthesis.
{focus_instruction}
## Collected Content
{content_section}

## Your Task

Generate a JSON response with:

1. "synthesis": A 1-3 paragraph natural language summary (string) covering:
   - Key macro themes emerging across sources
   - High-conviction ideas where multiple sources align
   - Notable contradictions or divergences
   - Any significant regime shifts or catalysts

2. "key_themes": Array of 3-7 key themes as strings (e.g., ["Fed policy pivot", "Tech sector rotation"])

3. "high_conviction_ideas": Array of objects, each with:
   - "idea": The investment idea (string)
   - "sources": Array of sources supporting it
   - "confidence": "high", "medium", or "low"
   - "rationale": Brief explanation (1-2 sentences)

4. "contradictions": Array of objects (can be empty), each with:
   - "topic": The topic with conflicting views
   - "views": Object mapping source name to their view

5. "market_regime": Current market regime assessment ("risk-on", "risk-off", "transitioning", "unclear")

6. "catalysts": Array of upcoming events/catalysts mentioned (can be empty)

Respond with valid JSON only."""

        return prompt

    def _empty_synthesis(self, time_window: str) -> Dict[str, Any]:
        """Return empty synthesis when no content available."""
        return {
            "synthesis": f"No content collected in the past {time_window}. Run collection to gather research data.",
            "key_themes": [],
            "high_conviction_ideas": [],
            "contradictions": [],
            "market_regime": "unclear",
            "catalysts": [],
            "time_window": time_window,
            "content_count": 0,
            "sources_included": [],
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }

    def generate_topic_synthesis(
        self,
        content_items: List[Dict[str, Any]],
        topic: str
    ) -> Dict[str, Any]:
        """
        Generate synthesis focused on a specific topic.

        Args:
            content_items: All available content
            topic: Specific topic to focus on (e.g., "gold", "volatility")

        Returns:
            Topic-focused synthesis
        """
        # Filter content relevant to topic
        relevant_items = []
        topic_lower = topic.lower()

        for item in content_items:
            # Check themes
            themes = item.get("themes", [])
            if any(topic_lower in t.lower() for t in themes):
                relevant_items.append(item)
                continue

            # Check tickers
            tickers = item.get("tickers", [])
            if any(topic_lower in t.lower() for t in tickers):
                relevant_items.append(item)
                continue

            # Check summary/content
            summary = item.get("summary", item.get("content_text", ""))
            if topic_lower in summary.lower():
                relevant_items.append(item)

        if not relevant_items:
            return {
                "synthesis": f"No content found related to '{topic}' in the collected research.",
                "key_themes": [],
                "high_conviction_ideas": [],
                "contradictions": [],
                "topic": topic,
                "content_count": 0,
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }

        return self.analyze(relevant_items, time_window="topic_search", focus_topic=topic)

    def get_source_view(
        self,
        content_items: List[Dict[str, Any]],
        source: str,
        topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a specific source's current view.

        Args:
            content_items: All available content
            source: Source name (e.g., "42macro")
            topic: Optional topic to filter by

        Returns:
            Source-specific view summary
        """
        # Filter to source
        source_items = [item for item in content_items if item.get("source") == source]

        if not source_items:
            return {
                "source": source,
                "view": f"No recent content from {source}.",
                "last_update": None,
                "themes": [],
                "sentiment": "unknown"
            }

        # Further filter by topic if provided
        if topic:
            topic_lower = topic.lower()
            filtered = []
            for item in source_items:
                themes = item.get("themes", [])
                summary = item.get("summary", item.get("content_text", ""))
                if any(topic_lower in t.lower() for t in themes) or topic_lower in summary.lower():
                    filtered.append(item)
            if filtered:
                source_items = filtered

        # Build prompt for source view
        prompt = f"""Based on the following recent content from {source}, summarize their current market view.

## Content from {source}:
"""
        for item in source_items[:5]:  # Limit to most recent 5
            title = item.get("title", "Untitled")
            summary = item.get("summary", "")[:300]
            themes = item.get("themes", [])
            prompt += f"\n**{title}**\nThemes: {', '.join(themes)}\nSummary: {summary}\n"

        topic_context = f" regarding {topic}" if topic else ""
        prompt += f"""
Generate a JSON response with:
1. "current_view": Their current market stance{topic_context} (1-2 sentences)
2. "key_themes": Array of themes they're focused on
3. "sentiment": Overall sentiment ("bullish", "bearish", "neutral", "mixed")
4. "notable_calls": Any specific trade ideas or calls they've made
5. "last_mentioned": Topic of most recent content

Respond with valid JSON only."""

        response = self.call_claude(
            prompt=prompt,
            system_prompt="You are summarizing a research source's market view. Be concise and accurate.",
            max_tokens=500,
            temperature=0.1,
            expect_json=True
        )

        response["source"] = source
        response["topic"] = topic
        response["content_count"] = len(source_items)

        return response

    # =========================================================================
    # V2 METHODS (PRD-020: Actionable Synthesis Enhancement)
    # =========================================================================

    def _extract_levels_from_content(self, content_items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Pre-scan content to extract specific levels, strikes, and dates.
        This helps Claude produce more specific output.

        Args:
            content_items: List of content items to scan

        Returns:
            Dict with extracted price_levels, option_strikes, dates, tickers
        """
        extracted = {
            "price_levels": [],
            "option_strikes": [],
            "dates": [],
            "tickers": []
        }

        for item in content_items:
            text = str(item.get("content_text", "")) + " " + str(item.get("summary", ""))

            # Extract price levels (4-5 digit numbers, likely prices)
            # Matches: 5950, 6000, 4500, 100.50, etc.
            prices = re.findall(r'\b([1-9]\d{2,4}(?:\.\d{1,2})?)\b', text)
            extracted["price_levels"].extend(prices)

            # Extract VIX levels (2-3 digit, typically 10-50 range)
            vix_levels = re.findall(r'\bVIX\s*(?:at|to|above|below|@)?\s*(\d{1,2}(?:\.\d{1,2})?)\b', text, re.I)
            extracted["price_levels"].extend([f"VIX {v}" for v in vix_levels])

            # Extract option mentions (e.g., "Dec 16 calls", "Jan 4500 puts", "6000C")
            options = re.findall(
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d+\s+(?:calls?|puts?))',
                text, re.I
            )
            extracted["option_strikes"].extend(options)

            # Also match strike format like "6000C" or "5900P"
            strike_format = re.findall(r'\b(\d{3,5}[CP])\b', text, re.I)
            extracted["option_strikes"].extend(strike_format)

            # Extract dates (various formats)
            dates = re.findall(
                r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:[,\s]+\d{4})?)',
                text, re.I
            )
            extracted["dates"].extend(dates)

            # Extract FOMC, CPI, NFP mentions
            events = re.findall(r'\b(FOMC|CPI|NFP|PCE|GDP|ISM)\b', text, re.I)
            for event in events:
                extracted["dates"].append(event.upper())

            # Tickers already extracted by classifier
            tickers = item.get("tickers", [])
            if isinstance(tickers, list):
                extracted["tickers"].extend(tickers)

        # Deduplicate and limit
        for key in extracted:
            # Remove empty strings and deduplicate
            extracted[key] = list(set(str(x).strip() for x in extracted[key] if x and str(x).strip()))
            # Limit to most common/relevant
            extracted[key] = extracted[key][:25]

        return extracted

    def _build_synthesis_prompt_v2(
        self,
        content_items: List[Dict[str, Any]],
        time_window: str,
        focus_topic: Optional[str] = None
    ) -> str:
        """Build enhanced prompt for actionable synthesis (v2)."""

        # Group content by source (PRD-040: use channel_display for YouTube)
        by_source = {}
        for item in content_items:
            source = item.get("source", "unknown")
            # PRD-040: Use channel display name for YouTube content
            if source == "youtube" and item.get("channel_display"):
                display_key = f"youtube:{item['channel_display']}"
            else:
                display_key = source
            if display_key not in by_source:
                by_source[display_key] = []
            by_source[display_key].append(item)

        # Build content summary section with source weights
        content_section = ""
        for source_key, items in by_source.items():
            # PRD-040: Extract display name and base source for weight lookup
            if source_key.startswith("youtube:"):
                channel_name = source_key.split(":", 1)[1]
                base_source = "youtube"
                weight = self.SOURCE_WEIGHTS_V2.get(base_source, 1.0)
                reliability = self.SOURCE_WEIGHTS.get(base_source, "medium")
                content_section += f"\n### YOUTUBE - {channel_name} (Weight: {weight}x, {reliability})\n"
            else:
                weight = self.SOURCE_WEIGHTS_V2.get(source_key, 1.0)
                reliability = self.SOURCE_WEIGHTS.get(source_key, "medium")
                content_section += f"\n### {source_key.upper()} (Weight: {weight}x, {reliability})\n"

            for item in items[:15]:  # Limit items per source
                title = item.get("title", "Untitled")
                content_type = item.get("type", item.get("content_type", "unknown"))
                timestamp = item.get("timestamp", item.get("collected_at", ""))
                summary = str(item.get("summary", item.get("content_text", "")))[:600]
                themes = item.get("themes", [])
                sentiment = item.get("sentiment", "")
                tickers = item.get("tickers", [])

                content_section += f"\n**{title}** ({content_type})\n"
                if timestamp:
                    content_section += f"Time: {timestamp}\n"
                if themes:
                    content_section += f"Themes: {', '.join(themes[:5])}\n"
                if sentiment:
                    content_section += f"Sentiment: {sentiment}\n"
                if tickers:
                    content_section += f"Tickers: {', '.join(tickers[:10])}\n"
                if summary:
                    content_section += f"Content: {summary}\n"

        # Extract specific levels to include in prompt
        extracted = self._extract_levels_from_content(content_items)

        extraction_section = ""
        if any(extracted.values()):
            extraction_section = f"""
## Pre-Extracted Data (incorporate these specific values into your output)

Price Levels Mentioned: {', '.join(extracted['price_levels'][:20]) or 'None found'}
Option Strikes Mentioned: {', '.join(extracted['option_strikes'][:15]) or 'None found'}
Dates/Events Mentioned: {', '.join(extracted['dates'][:15]) or 'None found'}
Tickers Mentioned: {', '.join(extracted['tickers'][:20]) or 'None found'}

IMPORTANT: Use these specific values in your tactical and strategic ideas. Do NOT use vague terms like "support" or "resistance" without the actual numbers.
"""

        # Focus instruction
        focus_instruction = ""
        if focus_topic:
            focus_instruction = f"\n\nFOCUS: Pay particular attention to content related to: {focus_topic}\n"

        prompt = f"""Analyze the following research content collected over the past {time_window} and generate an ACTIONABLE synthesis.
{focus_instruction}
## Source Content
{content_section}
{extraction_section}
## Required Output (JSON)

Generate a JSON response with ALL of these sections:

### 1. market_regime (required object)
{{
  "current": "risk-on" | "risk-off" | "transitioning" | "range-bound",
  "direction": "improving" | "deteriorating" | "stable",
  "confidence": 0.0-1.0,
  "key_drivers": ["driver1", "driver2", "driver3"]
}}

### 2. synthesis_summary (required string)
2-3 sentence executive summary of the current research landscape. Be specific.

### 3. tactical_ideas (required array, ideas with <4 week horizon)
For EACH tactical idea, include ALL of these fields:
{{
  "idea": "clear statement of the trade idea",
  "conviction_score": {{
    "raw": "X/Y sources",
    "weighted": 0.0-1.0,
    "sources_agreeing": ["source1", "source2"],
    "sources_disagreeing": ["source3"]
  }},
  "trade_structure": {{
    "instrument": "VIX|SPX|specific ticker",
    "direction": "long|short|spread",
    "structure": "outright|calendar spread|butterfly|strangle|etc",
    "entry_level": "SPECIFIC number or range from sources",
    "stop_level": "SPECIFIC number",
    "target_level": "SPECIFIC number or range"
  }},
  "time_horizon": "1-3 days|1-2 weeks|2-4 weeks|through [specific event]",
  "catalyst": "specific event driving this thesis",
  "invalidation": "what would make this thesis wrong - be specific",
  "rationale": "2-3 sentences explaining the thesis"
}}

### 4. strategic_ideas (required array, ideas with 1-6 month horizon)
{{
  "idea": "clear statement",
  "conviction_score": {{ same format as above }},
  "thesis": "longer explanation of the macro thesis (3-5 sentences)",
  "key_levels": {{
    "support": ["level1", "level2"],
    "resistance": ["level1", "level2"]
  }},
  "time_horizon": "1-3 months|3-6 months",
  "triggers": ["what would cause thesis acceleration"],
  "risks": ["what could derail this thesis"]
}}

### 5. watch_list (required array, topics where sources DISAGREE)
{{
  "topic": "the topic with conflicting views",
  "status": "conflicting" | "developing" | "monitoring",
  "bull_case": {{
    "view": "the bullish argument",
    "sources": ["source1"]
  }},
  "bear_case": {{
    "view": "the bearish argument",
    "sources": ["source2"]
  }},
  "resolution_trigger": "what would resolve this conflict",
  "weighted_lean": "slight bull|slight bear|neutral - based on source weights"
}}

### 6. catalyst_calendar (required array, upcoming events with SPECIFIC DATES)
{{
  "date": "YYYY-MM-DD",
  "event": "event name",
  "impact": "high" | "medium" | "low",
  "relevance": "which ideas this affects",
  "consensus": "what market expects",
  "risk_scenario": "what surprise would mean"
}}

Known December 2025 dates: NFP Dec 6, CPI Dec 11, FOMC Dec 17-18, Quad Witch Dec 19

### 7. source_summary (required object)
{{
  "total_sources": number,
  "total_items": number,
  "by_source": {{
    "source_name": {{
      "items": number,
      "weight": number,
      "current_stance": "1 sentence summary of their view"
    }}
  }}
}}

RESPOND WITH VALID JSON ONLY. Be SPECIFIC with all levels, dates, and numbers."""

        return prompt

    def _empty_synthesis_v2(self, time_window: str) -> Dict[str, Any]:
        """Return empty v2 synthesis when no content available."""
        return {
            "version": "2.0",
            "market_regime": {
                "current": "unclear",
                "direction": "stable",
                "confidence": 0.0,
                "key_drivers": []
            },
            "synthesis_summary": f"No content collected in the past {time_window}. Run collection to gather research data.",
            "tactical_ideas": [],
            "strategic_ideas": [],
            "watch_list": [],
            "catalyst_calendar": [],
            "source_summary": {
                "total_sources": 0,
                "total_items": 0,
                "by_source": {}
            },
            "time_window": time_window,
            "content_count": 0,
            "sources_included": [],
            "generated_at": datetime.utcnow().isoformat()
        }

    def analyze_v2(
        self,
        content_items: List[Dict[str, Any]],
        time_window: str = "24h",
        focus_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate actionable synthesis from collected content (V2).

        This is the enhanced version that provides:
        - Specific price levels and strikes
        - Quantified conviction with source weighting
        - Entry/stop/target for tactical ideas
        - Time-horizon bucketing
        - Catalyst calendar with dates
        - Watch list for conflicting views

        Args:
            content_items: List of analyzed content items to synthesize
            time_window: Time window being analyzed ("24h", "7d", "30d")
            focus_topic: Optional specific topic to focus on

        Returns:
            Actionable synthesis with structured output (v2 schema)
        """
        if not content_items:
            return self._empty_synthesis_v2(time_window)

        logger.info(f"Generating v2 synthesis for {len(content_items)} items over {time_window}")

        # Build the enhanced prompt
        prompt = self._build_synthesis_prompt_v2(content_items, time_window, focus_topic)

        # Call Claude with v2 system prompt
        response = self.call_claude(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT_V2,
            max_tokens=4000,  # Larger output for detailed structure
            temperature=0.2,  # Lower temp for more consistent structure
            expect_json=True
        )

        # Add metadata
        response["version"] = "2.0"
        response["time_window"] = time_window
        response["content_count"] = len(content_items)
        response["sources_included"] = list(set(item.get("source", "unknown") for item in content_items))
        response["generated_at"] = datetime.utcnow().isoformat()
        if focus_topic:
            response["focus_topic"] = focus_topic

        # Validate required v2 fields
        required_fields = [
            "market_regime",
            "synthesis_summary",
            "tactical_ideas",
            "strategic_ideas",
            "watch_list",
            "catalyst_calendar"
        ]

        try:
            self.validate_response_schema(response, required_fields)
        except Exception as e:
            logger.warning(f"V2 schema validation failed: {e}, returning partial response")

        logger.info(f"Generated v2 synthesis: {len(response.get('tactical_ideas', []))} tactical, "
                   f"{len(response.get('strategic_ideas', []))} strategic ideas")

        return response


    # =========================================================================
    # V3 METHODS (PRD-021: Research Consumption Hub)
    # =========================================================================

    def _build_synthesis_prompt_v3(
        self,
        content_items: List[Dict[str, Any]],
        time_window: str,
        older_content: Optional[List[Dict[str, Any]]] = None,
        focus_topic: Optional[str] = None
    ) -> str:
        """Build prompt for research consumption synthesis (v3)."""

        # Group content by source (PRD-040: use channel_display for YouTube)
        by_source = {}
        for item in content_items:
            source = item.get("source", "unknown")
            # PRD-040: Use channel display name for YouTube content
            if source == "youtube" and item.get("channel_display"):
                display_key = f"youtube:{item['channel_display']}"
            else:
                display_key = source
            if display_key not in by_source:
                by_source[display_key] = []
            by_source[display_key].append(item)

        # Build content summary section
        content_section = ""
        for source_key, items in by_source.items():
            # PRD-040: Extract display name and base source for weight lookup
            if source_key.startswith("youtube:"):
                channel_name = source_key.split(":", 1)[1]
                base_source = "youtube"
                weight = self.SOURCE_WEIGHTS_V2.get(base_source, 1.0)
                content_section += f"\n### YOUTUBE - {channel_name} (Weight: {weight}x)\n"
            else:
                weight = self.SOURCE_WEIGHTS_V2.get(source_key, 1.0)
                content_section += f"\n### {source_key.upper()} (Weight: {weight}x)\n"

            for item in items[:15]:
                title = item.get("title", "Untitled")
                content_type = item.get("type", item.get("content_type", "unknown"))
                timestamp = item.get("timestamp", item.get("collected_at", ""))
                summary = str(item.get("summary", item.get("content_text", "")))[:600]
                themes = item.get("themes", [])
                sentiment = item.get("sentiment", "")

                content_section += f"\n**{title}** ({content_type})\n"
                if timestamp:
                    content_section += f"Time: {timestamp}\n"
                if themes:
                    content_section += f"Themes: {', '.join(themes[:5])}\n"
                if sentiment:
                    content_section += f"Sentiment: {sentiment}\n"
                if summary:
                    content_section += f"Content: {summary}\n"

        # Build older content section for re-review recommendations
        older_section = ""
        if older_content:
            older_section = "\n## OLDER CONTENT (7-30 days ago) - scan for re-review candidates\n"
            # PRD-040: Group older content by channel_display for YouTube
            older_by_source = {}
            for item in older_content:
                source = item.get("source", "unknown")
                # PRD-040: Use channel display name for YouTube content
                if source == "youtube" and item.get("channel_display"):
                    display_key = f"youtube:{item['channel_display']}"
                else:
                    display_key = source
                if display_key not in older_by_source:
                    older_by_source[display_key] = []
                older_by_source[display_key].append(item)

            for source_key, items in older_by_source.items():
                # PRD-040: Format header with channel name for YouTube
                if source_key.startswith("youtube:"):
                    channel_name = source_key.split(":", 1)[1]
                    older_section += f"\n### YOUTUBE - {channel_name} (older)\n"
                else:
                    older_section += f"\n### {source_key.upper()} (older)\n"
                for item in items[:10]:
                    title = item.get("title", "Untitled")
                    timestamp = item.get("timestamp", item.get("collected_at", ""))
                    themes = item.get("themes", [])
                    summary = str(item.get("summary", ""))[:300]
                    older_section += f"- **{title}** ({timestamp}): {', '.join(themes[:3])}. {summary[:150]}...\n"

        # Extract levels for reference
        extracted = self._extract_levels_from_content(content_items)

        focus_instruction = ""
        if focus_topic:
            focus_instruction = f"\n\nFOCUS: Pay particular attention to content related to: {focus_topic}\n"

        prompt = f"""Analyze the following research content collected over the past {time_window} and generate a RESEARCH CONSUMPTION synthesis.

Remember: You are helping the user CONSUME their research, not telling them what to trade.
{focus_instruction}
## RECENT CONTENT (past {time_window})
{content_section}
{older_section}
## EXTRACTED REFERENCE DATA
Price levels mentioned: {', '.join(extracted['price_levels'][:15]) or 'None'}
Key events mentioned: {', '.join(extracted['dates'][:10]) or 'None'}

## REQUIRED OUTPUT (JSON)

### 1. executive_summary (required object - COMPREHENSIVE FORMAT)
{{
  "macro_context": "1-2 sentences setting the stage for what's happening in markets right now. E.g., 'Markets are navigating the final trading days before FOMC amid mixed signals on inflation trajectory.'",

  "source_highlights": {{
    "42macro": "2-3 sentences on 42Macro's current stance. What is Darius focusing on? What's his framework saying?",
    "discord": "2-3 sentences on Discord's current focus. What is Imran positioned for? What structures is he using?",
    "kt_technical": "2-3 sentences on KT Technical's view. What do the Elliott Wave counts show? Key levels?",
    "youtube": "1-2 sentences if relevant content, otherwise null",
    "substack": "1-2 sentences if relevant content, otherwise null"
  }},

  "synthesis_narrative": "2-3 PARAGRAPHS connecting the dots across all sources:\\n\\nParagraph 1: Where sources ALIGN (confluence). What themes do multiple sources agree on?\\n\\nParagraph 2: Where sources DIFFER and what that means. What conflicts exist and how might they resolve?\\n\\nParagraph 3: What deserves attention and why. What's the overall picture?",

  "key_takeaways": [
    "Takeaway 1: Most important insight (be specific with levels/dates)",
    "Takeaway 2: Second most important insight",
    "Takeaway 3: Third insight",
    "Takeaway 4: Optional fourth insight",
    "Takeaway 5: Optional fifth insight"
  ],

  "overall_tone": "bullish|bearish|neutral|cautious|uncertain|transitioning",
  "dominant_theme": "The single most important theme across sources"
}}

### 2. confluence_zones (required array)
Where do independent sources ALIGN on a theme or view? This is the core value.
{{
  "theme": "The theme/view where sources align",
  "confluence_strength": 0.0-1.0 (based on source count and weights),
  "sources_aligned": [
    {{
      "source": "source_name",
      "view": "What this source says about it (1 sentence)"
    }}
  ],
  "sources_contrary": [
    {{
      "source": "source_name",
      "view": "The contrary view if any"
    }}
  ],
  "relevant_levels": ["Specific price levels mentioned if any"],
  "related_catalyst": "Upcoming event related to this theme or null"
}}

### 3. conflict_watch (required array)
Where do sources DISAGREE? These are important to monitor.
{{
  "topic": "The topic with conflicting views",
  "status": "active_conflict|developing|monitoring",
  "bull_case": {{
    "view": "The bullish argument",
    "sources": ["source1"]
  }},
  "bear_case": {{
    "view": "The bearish argument",
    "sources": ["source2"]
  }},
  "resolution_trigger": "What event/data would resolve this conflict",
  "weighted_lean": "slight_bull|slight_bear|neutral (based on source weights)",
  "user_action": "What the user should monitor"
}}

### 4. attention_priorities (required array, MAX 5 items)
Ranked list of what deserves the user's focus. Most important first.
{{
  "rank": 1-5,
  "focus_area": "What to focus on (instrument, theme, or event)",
  "why": "Why this deserves attention right now (1-2 sentences)",
  "sources_discussing": ["list of sources covering this"],
  "time_sensitivity": "immediate|high|medium|low"
}}

### 5. re_review_recommendations (required array, 3-5 items)
Identify OLDER content that is NOW more relevant due to current conditions.
Relevance triggers: catalyst_approaching, level_being_tested, scenario_playing_out, conflict_resolving
{{
  "source": "source_name",
  "content_date": "approximate date",
  "title": "content title or description",
  "why_relevant_now": "2-3 sentences explaining why this older content is worth revisiting NOW",
  "themes_mentioned": ["theme1", "theme2"],
  "relevance_trigger": "catalyst_approaching|level_being_tested|scenario_playing_out|conflict_resolving"
}}

### 6. source_stances (required object)
Narrative summary of what each source is currently thinking.
{{
  "source_name": {{
    "weight": numeric weight,
    "items_analyzed": count,
    "current_stance_narrative": "2-3 sentences in narrative form describing what this source/person is thinking and focused on. Write like: 'Imran is positioned for X. He sees Y and is expressing this via Z.'",
    "key_themes": ["theme1", "theme2"],
    "overall_bias": "bullish|bearish|cautious|neutral|mixed"
  }}
}}

### 7. catalyst_calendar (required array)
Upcoming events with source perspectives.
{{
  "date": "YYYY-MM-DD",
  "event": "Event name",
  "impact": "high|medium|low",
  "source_perspectives": [
    {{
      "source": "source_name",
      "view": "What this source said about this event"
    }}
  ],
  "themes_affected": ["Which confluence zones this impacts"],
  "pre_event_review": "Specific older content to review before this event, or null"
}}

Known December 2025 dates: NFP Dec 6, CPI Dec 11, FOMC Dec 17-18, Quad Witch Dec 19

RESPOND WITH VALID JSON ONLY."""

        return prompt

    def _empty_synthesis_v3(self, time_window: str) -> Dict[str, Any]:
        """Return empty v3 synthesis when no content available."""
        return {
            "version": "3.0",
            "executive_summary": {
                "macro_context": f"No content collected in the past {time_window}.",
                "source_highlights": {},
                "synthesis_narrative": "Run collection to gather research data.",
                "key_takeaways": [],
                "overall_tone": "uncertain",
                "dominant_theme": None
            },
            "confluence_zones": [],
            "conflict_watch": [],
            "attention_priorities": [],
            "re_review_recommendations": [],
            "source_stances": {},
            "catalyst_calendar": [],
            "time_window": time_window,
            "content_count": 0,
            "sources_included": [],
            "generated_at": datetime.utcnow().isoformat()
        }

    def analyze_v3(
        self,
        content_items: List[Dict[str, Any]],
        older_content: Optional[List[Dict[str, Any]]] = None,
        time_window: str = "24h",
        focus_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate research consumption synthesis (V3 - PRD-021).

        This version focuses on helping users consume their research:
        - Executive summary of what sources are saying
        - Confluence zones where sources align
        - Conflict watch for disagreements
        - Attention priorities for focus
        - Re-review recommendations for older relevant content
        - Source stances in narrative form

        Args:
            content_items: Recent content items (within time_window)
            older_content: Older content (7-30 days) for re-review scanning
            time_window: Time window being analyzed ("24h", "7d", "30d")
            focus_topic: Optional specific topic to focus on

        Returns:
            Research consumption synthesis (v3 schema)
        """
        if not content_items:
            return self._empty_synthesis_v3(time_window)

        logger.info(f"Generating v3 synthesis for {len(content_items)} items over {time_window}")
        if older_content:
            logger.info(f"Including {len(older_content)} older items for re-review scanning")

        # Build the v3 prompt
        prompt = self._build_synthesis_prompt_v3(
            content_items,
            time_window,
            older_content=older_content,
            focus_topic=focus_topic
        )

        # Call Claude with v3 system prompt
        # Increased max_tokens for enhanced executive summary (PRD-025)
        response = self.call_claude(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT_V3,
            max_tokens=5000,
            temperature=0.25,
            expect_json=True
        )

        # Add metadata
        response["version"] = "3.0"
        response["time_window"] = time_window
        response["content_count"] = len(content_items)
        response["older_content_scanned"] = len(older_content) if older_content else 0
        response["sources_included"] = list(set(item.get("source", "unknown") for item in content_items))
        response["generated_at"] = datetime.utcnow().isoformat()
        if focus_topic:
            response["focus_topic"] = focus_topic

        # Validate required v3 fields
        required_fields = [
            "executive_summary",
            "confluence_zones",
            "conflict_watch",
            "attention_priorities",
            "re_review_recommendations",
            "source_stances",
            "catalyst_calendar"
        ]

        try:
            self.validate_response_schema(response, required_fields)
        except Exception as e:
            logger.warning(f"V3 schema validation failed: {e}, returning partial response")

        logger.info(f"Generated v3 synthesis: {len(response.get('confluence_zones', []))} confluence zones, "
                   f"{len(response.get('attention_priorities', []))} priorities")

        return response

    # =========================================================================
    # V4 METHODS (PRD-041: Tiered Synthesis)
    # =========================================================================

    def _build_source_breakdown_prompt(
        self,
        content_items: List[Dict[str, Any]],
        source_key: str
    ) -> str:
        """Build prompt for generating a source breakdown (Tier 2)."""

        # Get items for this source
        items = [item for item in content_items if self._get_source_key(item) == source_key]

        content_text = ""
        for item in items[:10]:  # Limit to 10 items per source
            title = item.get("title", "Untitled")
            content_type = item.get("type", item.get("content_type", "unknown"))
            timestamp = item.get("timestamp", item.get("collected_at", ""))
            summary = str(item.get("summary", item.get("content_text", "")))[:800]
            themes = item.get("themes", [])
            sentiment = item.get("sentiment", "")

            content_text += f"\n### {title} ({content_type})\n"
            if timestamp:
                content_text += f"Time: {timestamp}\n"
            if themes:
                content_text += f"Themes: {', '.join(themes[:5])}\n"
            if sentiment:
                content_text += f"Sentiment: {sentiment}\n"
            if summary:
                content_text += f"Content: {summary}\n"

        return f"""Generate a detailed breakdown for content from {source_key}.

CONTENT TO ANALYZE:
{content_text}

Generate a JSON response with:
{{
  "summary": "3-5 sentences covering the key insights from this source. Be specific about topics discussed, levels mentioned, and conclusions drawn.",
  "key_insights": [
    "Specific insight 1 (with any numbers/levels mentioned)",
    "Specific insight 2",
    "Specific insight 3",
    "Specific insight 4 (if applicable)",
    "Specific insight 5 (if applicable)"
  ],
  "themes": ["theme1", "theme2", "theme3"],
  "overall_bias": "bullish|bearish|neutral|mixed|cautious",
  "content_titles": ["Title 1", "Title 2", ...]
}}

Be SPECIFIC. Include price levels, dates, and key data points mentioned in the content.
Respond with valid JSON only."""

    def _get_source_key(self, item: Dict[str, Any]) -> str:
        """Get the source key for an item, with YouTube channel granularity."""
        source = item.get("source", "unknown")
        if source == "youtube" and item.get("channel_display"):
            return f"youtube:{item['channel_display']}"
        return source

    def _generate_content_summaries(
        self,
        content_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate Tier 3 content summaries from existing analyzed content.

        Uses analysis_result.content_summary if available, otherwise generates minimal summary.
        """
        summaries = []

        for item in content_items:
            content_id = item.get("id", item.get("content_id"))

            # Check if there's a pre-computed content summary
            analysis = item.get("analysis_result", {})
            if isinstance(analysis, str):
                try:
                    import json
                    analysis = json.loads(analysis)
                except:
                    analysis = {}

            content_summary = analysis.get("content_summary", {})

            summary_entry = {
                "id": content_id,
                "source": item.get("source", "unknown"),
                "channel": item.get("channel_display"),
                "title": item.get("title", "Untitled"),
                "collected_at": item.get("collected_at", item.get("timestamp", "")),
                "content_type": item.get("type", item.get("content_type", "unknown")),
                "summary": content_summary.get("summary") or item.get("summary", "")[:300],
                "themes": content_summary.get("themes") or item.get("themes", []),
                "key_points": content_summary.get("key_points", []),
                "tickers_mentioned": item.get("tickers", []),
                "sentiment": item.get("sentiment", "neutral")
            }

            summaries.append(summary_entry)

        return summaries

    def _empty_synthesis_v4(self, time_window: str) -> Dict[str, Any]:
        """Return empty v4 synthesis when no content available."""
        return {
            "version": "4.0",
            "executive_summary": {
                "macro_context": f"No content collected in the past {time_window}.",
                "synthesis_narrative": "Run collection to gather research data.",
                "key_takeaways": [],
                "overall_tone": "uncertain",
                "dominant_theme": None
            },
            "confluence_zones": [],
            "conflict_watch": [],
            "attention_priorities": [],
            "catalyst_calendar": [],
            "source_breakdowns": {},
            "content_summaries": [],
            "time_window": time_window,
            "content_count": 0,
            "sources_included": [],
            "youtube_channels_included": [],
            "generated_at": datetime.utcnow().isoformat()
        }

    def analyze_v4(
        self,
        content_items: List[Dict[str, Any]],
        older_content: Optional[List[Dict[str, Any]]] = None,
        time_window: str = "24h",
        focus_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate tiered synthesis (V4 - PRD-041).

        Returns three tiers of detail:
        - Tier 1: Executive summary, confluence zones, conflicts, priorities
        - Tier 2: Per-source detailed breakdowns (YouTube by channel)
        - Tier 3: Per-content item summaries

        Args:
            content_items: Recent content items (within time_window)
            older_content: Older content (7-30 days) for re-review scanning
            time_window: Time window being analyzed ("24h", "7d", "30d")
            focus_topic: Optional specific topic to focus on

        Returns:
            Tiered synthesis (v4 schema)
        """
        if not content_items:
            return self._empty_synthesis_v4(time_window)

        logger.info(f"Generating v4 tiered synthesis for {len(content_items)} items over {time_window}")

        # TIER 1: Generate executive summary using V3 (existing logic)
        tier1_response = self.analyze_v3(
            content_items=content_items,
            older_content=older_content,
            time_window=time_window,
            focus_topic=focus_topic
        )

        # TIER 2: Generate source breakdowns
        # Group content by source (with YouTube channel granularity)
        source_groups = {}
        for item in content_items:
            source_key = self._get_source_key(item)
            if source_key not in source_groups:
                source_groups[source_key] = []
            source_groups[source_key].append(item)

        source_breakdowns = {}
        youtube_channels = []

        for source_key, items in source_groups.items():
            # Get base source and weight
            if source_key.startswith("youtube:"):
                channel_name = source_key.split(":", 1)[1]
                base_source = "youtube"
                youtube_channels.append(channel_name)
            else:
                base_source = source_key
                channel_name = None

            weight = self.SOURCE_WEIGHTS_V2.get(base_source, 1.0)

            # Generate breakdown for this source
            try:
                prompt = self._build_source_breakdown_prompt(content_items, source_key)
                breakdown = self.call_claude(
                    prompt=prompt,
                    system_prompt="You are summarizing research content from a specific source. Be specific and include key data points.",
                    max_tokens=1500,
                    temperature=0.2,
                    expect_json=True
                )
            except Exception as e:
                logger.warning(f"Failed to generate breakdown for {source_key}: {e}")
                breakdown = {
                    "summary": f"Content from {source_key}",
                    "key_insights": [],
                    "themes": [],
                    "overall_bias": "neutral",
                    "content_titles": [item.get("title", "Untitled") for item in items]
                }

            # Add metadata
            breakdown["weight"] = weight
            breakdown["content_count"] = len(items)

            source_breakdowns[source_key] = breakdown

        # TIER 3: Generate content summaries
        content_summaries = self._generate_content_summaries(content_items)

        # Combine all tiers
        result = {
            "version": "4.0",

            # TIER 1: Executive Summary
            "executive_summary": tier1_response.get("executive_summary", {}),
            "confluence_zones": tier1_response.get("confluence_zones", []),
            "conflict_watch": tier1_response.get("conflict_watch", []),
            "attention_priorities": tier1_response.get("attention_priorities", []),
            "catalyst_calendar": tier1_response.get("catalyst_calendar", []),
            "re_review_recommendations": tier1_response.get("re_review_recommendations", []),

            # TIER 2: Source Breakdowns
            "source_breakdowns": source_breakdowns,

            # TIER 3: Content Summaries
            "content_summaries": content_summaries,

            # Metadata
            "time_window": time_window,
            "content_count": len(content_items),
            "older_content_scanned": len(older_content) if older_content else 0,
            "sources_included": list(set(item.get("source", "unknown") for item in content_items)),
            "youtube_channels_included": youtube_channels,
            "generated_at": datetime.utcnow().isoformat()
        }

        if focus_topic:
            result["focus_topic"] = focus_topic

        logger.info(f"Generated v4 synthesis: {len(source_breakdowns)} source breakdowns, "
                   f"{len(content_summaries)} content summaries, "
                   f"{len(youtube_channels)} YouTube channels")

        return result


# Convenience function for quick synthesis
def generate_synthesis(
    content_items: List[Dict[str, Any]],
    time_window: str = "24h",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate synthesis without instantiating agent.

    Args:
        content_items: List of analyzed content
        time_window: Time window ("24h", "7d", "30d")
        api_key: Optional API key

    Returns:
        Synthesis result
    """
    agent = SynthesisAgent(api_key=api_key)
    return agent.analyze(content_items, time_window=time_window)
