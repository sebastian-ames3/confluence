"""
Synthesis Agent

Generates human-readable research synthesis from collected content.
Uses an experienced macro analyst persona to naturally weight evidence
and produce concise summaries of investment themes.

This agent replaces the complex confluence scoring UI with natural
language synthesis that Claude generates using internal judgment.
"""

import os
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

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514"
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

        # Group content by source
        by_source = {}
        for item in content_items:
            source = item.get("source", "unknown")
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(item)

        # Build content summary section
        content_section = ""
        for source, items in by_source.items():
            reliability = self.SOURCE_WEIGHTS.get(source, "medium")
            content_section += f"\n### {source.upper()} (Reliability: {reliability})\n"

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
