"""
Synthesis Agent

Generates research synthesis from collected content using a research assistant
persona. Produces executive summaries, confluence zones, conflict analysis,
per-source breakdowns, and content summaries in a single unified pipeline.

One method, one prompt, one output schema.
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

    Produces a comprehensive synthesis including:
    - Executive summary with per-source highlights
    - Confluence zones where sources align
    - Conflict watch for disagreements
    - Attention priorities
    - Re-review recommendations for older content
    - Per-source detailed breakdowns
    - Per-content item summaries
    - Catalyst calendar
    """

    SYSTEM_PROMPT = """You are a research assistant helping a sophisticated investor efficiently consume multiple paid research services.

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

    SOURCE_WEIGHTS = {
        "42macro": 1.5,      # Darius Dale - institutional-grade
        "discord": 1.5,      # Options Insight - professional options
        "kt_technical": 1.2, # Systematic technical analysis
        "substack": 1.0,     # Visser Labs - macro/crypto
        "youtube": 0.8       # Variable quality
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-5-20251101"
    ):
        """Initialize Synthesis Agent with Opus model."""
        super().__init__(api_key=api_key, model=model)
        logger.info("Initialized SynthesisAgent")

    def analyze(
        self,
        content_items: List[Dict[str, Any]],
        older_content: Optional[List[Dict[str, Any]]] = None,
        time_window: str = "24h",
        focus_topic: Optional[str] = None,
        kt_symbol_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive research synthesis.

        Performs three steps:
        1. Main synthesis call — executive summary, confluence zones, conflicts,
           priorities, re-review recommendations, catalyst calendar
        2. Per-source breakdown calls — detailed analysis per source/channel
        3. Content summary reshaping — per-item summaries from existing data

        Args:
            content_items: Recent content items (within time_window)
            older_content: Older content (7-30 days) for re-review scanning
            time_window: Time window being analyzed ("24h", "7d", "30d")
            focus_topic: Optional specific topic to focus on
            kt_symbol_data: KT Technical symbol-level data (wave counts, levels, bias)

        Returns:
            Unified synthesis dict with all sections
        """
        if not content_items:
            return self._empty_synthesis(time_window)

        logger.info(f"Generating synthesis for {len(content_items)} items over {time_window}")
        if older_content:
            logger.info(f"Including {len(older_content)} older items for re-review scanning")
        if kt_symbol_data:
            logger.info(f"Including KT Technical data for {len(kt_symbol_data)} symbols")

        # STEP 1: Main synthesis call
        prompt = self._build_prompt(
            content_items, time_window,
            older_content=older_content,
            focus_topic=focus_topic,
            kt_symbol_data=kt_symbol_data
        )

        response = self.call_claude(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            max_tokens=16000,
            temperature=0.25,
            expect_json=True
        )

        # Validate core fields
        required_fields = [
            "executive_summary",
            "confluence_zones",
            "conflict_watch",
            "attention_priorities",
            "re_review_recommendations",
            "catalyst_calendar"
        ]
        try:
            self.validate_response_schema(response, required_fields)
        except Exception as e:
            logger.warning(f"Schema validation failed: {e}, continuing with partial response")
            response["validation_passed"] = False
            response["validation_error"] = str(e)

        # STEP 2: Per-source breakdowns
        source_groups = {}
        for item in content_items:
            source_key = self._get_source_key(item)
            source_groups.setdefault(source_key, []).append(item)

        source_breakdowns = {}
        youtube_channels = []

        for source_key, items in source_groups.items():
            if source_key.startswith("youtube:"):
                youtube_channels.append(source_key.split(":", 1)[1])
                base_source = "youtube"
            else:
                base_source = source_key

            weight = self.SOURCE_WEIGHTS.get(base_source, 1.0)

            try:
                breakdown_prompt = self._build_source_breakdown_prompt(content_items, source_key)
                breakdown = self.call_claude(
                    prompt=breakdown_prompt,
                    system_prompt="You are summarizing research content from a specific source. Be specific and include key data points, levels, and quotes.",
                    max_tokens=4000,
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
                    "content_titles": [item.get("title", "Untitled") for item in items],
                    "degraded": True,
                    "degradation_reason": str(e)
                }

            breakdown["weight"] = weight
            breakdown["content_count"] = len(items)
            source_breakdowns[source_key] = breakdown

        # STEP 3: Content summaries (no LLM call)
        content_summaries = self._generate_content_summaries(content_items)

        # Combine into unified result
        result = {
            "executive_summary": response.get("executive_summary", {}),
            "confluence_zones": response.get("confluence_zones", []),
            "conflict_watch": response.get("conflict_watch", []),
            "attention_priorities": response.get("attention_priorities", []),
            "catalyst_calendar": response.get("catalyst_calendar", []),
            "re_review_recommendations": response.get("re_review_recommendations", []),
            "source_breakdowns": source_breakdowns,
            "content_summaries": content_summaries,
            "time_window": time_window,
            "content_count": len(content_items),
            "older_content_scanned": len(older_content) if older_content else 0,
            "sources_included": list(set(item.get("source", "unknown") for item in content_items)),
            "youtube_channels_included": youtube_channels,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }

        if focus_topic:
            result["focus_topic"] = focus_topic

        if response.get("validation_passed") is False:
            result["validation_passed"] = False
            result["validation_error"] = response.get("validation_error")

        logger.info(
            f"Generated synthesis: {len(response.get('confluence_zones', []))} confluence zones, "
            f"{len(source_breakdowns)} source breakdowns, "
            f"{len(content_summaries)} content summaries, "
            f"{len(youtube_channels)} YouTube channels"
        )

        return result

    # =========================================================================
    # PROMPT BUILDERS
    # =========================================================================

    def _build_prompt(
        self,
        content_items: List[Dict[str, Any]],
        time_window: str,
        older_content: Optional[List[Dict[str, Any]]] = None,
        focus_topic: Optional[str] = None,
        kt_symbol_data: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build the main synthesis prompt."""

        # Group content by source (with YouTube channel granularity)
        by_source = {}
        for item in content_items:
            display_key = self._get_source_key(item)
            by_source.setdefault(display_key, []).append(item)

        # Build content section
        content_section = ""
        for source_key, items in by_source.items():
            if source_key.startswith("youtube:"):
                channel_name = source_key.split(":", 1)[1]
                base_source = "youtube"
                weight = self.SOURCE_WEIGHTS.get(base_source, 1.0)
                content_section += f"\n### YOUTUBE - {channel_name} (Weight: {weight}x)\n"
            else:
                weight = self.SOURCE_WEIGHTS.get(source_key, 1.0)
                content_section += f"\n### {source_key.upper()} (Weight: {weight}x)\n"

            for item in items:
                title = item.get("title", "Untitled")
                content_type = item.get("type", item.get("content_type", "unknown"))
                timestamp = item.get("timestamp", item.get("collected_at", ""))
                summary = str(item.get("summary", ""))
                content_text_raw = str(item.get("content_text", ""))
                themes = item.get("themes", [])
                sentiment = item.get("sentiment", "")
                key_quotes = item.get("key_quotes", [])

                content_section += f"\n**{title}** ({content_type})\n"
                if timestamp:
                    content_section += f"Time: {timestamp}\n"
                if themes:
                    content_section += f"Themes: {', '.join(themes[:5])}\n"
                if sentiment:
                    content_section += f"Sentiment: {sentiment}\n"
                if summary:
                    content_section += f"Summary: {summary}\n"
                if key_quotes:
                    content_section += "Key Quotes:\n"
                    for quote in key_quotes[:5]:
                        if isinstance(quote, dict):
                            speaker = quote.get("speaker", "")
                            text = quote.get("text", quote.get("quote", ""))
                            ts = quote.get("timestamp", "")
                            prefix = f"[{speaker}]" if speaker else ""
                            if ts:
                                prefix = f"[{ts}] {prefix}" if prefix else f"[{ts}]"
                            content_section += f"  - {prefix} \"{text}\"\n"
                        elif isinstance(quote, str):
                            content_section += f"  - \"{quote}\"\n"
                if content_text_raw:
                    content_section += f"Transcript/Content:\n{content_text_raw}\n"

        # Older content section for re-review recommendations
        older_section = ""
        if older_content:
            older_section = "\n## OLDER CONTENT (7-30 days ago) - scan for re-review candidates\n"
            older_by_source = {}
            for item in older_content:
                display_key = self._get_source_key(item)
                older_by_source.setdefault(display_key, []).append(item)

            for source_key, items in older_by_source.items():
                if source_key.startswith("youtube:"):
                    channel_name = source_key.split(":", 1)[1]
                    older_section += f"\n### YOUTUBE - {channel_name} (older)\n"
                else:
                    older_section += f"\n### {source_key.upper()} (older)\n"
                for item in items:
                    title = item.get("title", "Untitled")
                    timestamp = item.get("timestamp", item.get("collected_at", ""))
                    themes = item.get("themes", [])
                    summary = str(item.get("summary", ""))
                    older_section += f"- **{title}** ({timestamp}): {', '.join(themes[:3])}. {summary}\n"

        # Extract levels for reference
        extracted = self._extract_levels_from_content(content_items)

        # KT Technical symbol data section
        kt_symbol_section = ""
        if kt_symbol_data:
            kt_symbol_section = "\n## KT TECHNICAL SYMBOL-LEVEL DATA\n"
            kt_symbol_section += "The following structured Elliott Wave analysis data is extracted from KT Technical. Use this to provide SPECIFIC levels and wave counts in the synthesis.\n\n"
            for sym_data in kt_symbol_data:
                symbol = sym_data.get("symbol", "UNKNOWN")
                kt_symbol_section += f"### {symbol}\n"
                if sym_data.get("wave_position"):
                    kt_symbol_section += f"- Wave Position: {sym_data['wave_position']}\n"
                if sym_data.get("wave_direction"):
                    kt_symbol_section += f"- Wave Direction: {sym_data['wave_direction']}\n"
                if sym_data.get("wave_phase"):
                    kt_symbol_section += f"- Wave Phase: {sym_data['wave_phase']}\n"
                if sym_data.get("bias"):
                    kt_symbol_section += f"- Bias: {sym_data['bias']}\n"
                if sym_data.get("primary_target"):
                    kt_symbol_section += f"- Primary Target: {sym_data['primary_target']}\n"
                if sym_data.get("primary_support"):
                    kt_symbol_section += f"- Primary Support: {sym_data['primary_support']}\n"
                if sym_data.get("invalidation"):
                    kt_symbol_section += f"- Invalidation Level: {sym_data['invalidation']}\n"
                if sym_data.get("notes"):
                    kt_symbol_section += f"- Notes: {sym_data['notes']}\n"
                if sym_data.get("last_updated"):
                    kt_symbol_section += f"- Last Updated: {sym_data['last_updated']}\n"
                kt_symbol_section += "\n"

        focus_instruction = ""
        if focus_topic:
            focus_instruction = f"\n\nFOCUS: Pay particular attention to content related to: {focus_topic}\n"

        prompt = f"""Analyze the following research content collected over the past {time_window} and generate a RESEARCH CONSUMPTION synthesis.

Remember: You are helping the user CONSUME their research, not telling them what to trade.
{focus_instruction}
## RECENT CONTENT (past {time_window})
{content_section}
{older_section}
{kt_symbol_section}
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
    "youtube_moonshots": "1-2 sentences on Moonshots (Peter Diamandis) content if present, otherwise null. Focus: AI, technology, abundance.",
    "youtube_forward_guidance": "1-2 sentences on Forward Guidance content if present, otherwise null. Focus: Macro, Fed policy.",
    "youtube_jordi_visser": "1-2 sentences on Jordi Visser Labs content if present, otherwise null. Focus: Information synthesis, macro.",
    "youtube_42macro": "1-2 sentences on 42 Macro video content if present, otherwise null. Focus: Institutional macro (video format of written research).",
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

### 6. catalyst_calendar (required array)
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

Economic calendar patterns: NFP is first Friday of month, CPI is typically 10th-13th, FOMC meets ~8x/year (check Fed calendar), Quad Witch is 3rd Friday of Mar/Jun/Sep/Dec.

RESPOND WITH VALID JSON ONLY."""

        return prompt

    def _build_source_breakdown_prompt(
        self,
        content_items: List[Dict[str, Any]],
        source_key: str
    ) -> str:
        """Build prompt for generating a per-source detailed breakdown."""

        items = [item for item in content_items if self._get_source_key(item) == source_key]

        content_text = ""
        for item in items:
            title = item.get("title", "Untitled")
            content_type = item.get("type", item.get("content_type", "unknown"))
            timestamp = item.get("timestamp", item.get("collected_at", ""))
            summary = str(item.get("summary", ""))
            content_text_raw = str(item.get("content_text", ""))
            themes = item.get("themes", [])
            sentiment = item.get("sentiment", "")
            key_quotes = item.get("key_quotes", [])

            content_text += f"\n### {title} ({content_type})\n"
            if timestamp:
                content_text += f"Time: {timestamp}\n"
            if themes:
                content_text += f"Themes: {', '.join(themes[:5])}\n"
            if sentiment:
                content_text += f"Sentiment: {sentiment}\n"
            if summary:
                content_text += f"Summary: {summary}\n"
            if key_quotes:
                content_text += "Key Quotes:\n"
                for quote in key_quotes[:5]:
                    if isinstance(quote, dict):
                        speaker = quote.get("speaker", "")
                        text = quote.get("text", quote.get("quote", ""))
                        ts = quote.get("timestamp", "")
                        prefix = f"[{speaker}]" if speaker else ""
                        if ts:
                            prefix = f"[{ts}] {prefix}" if prefix else f"[{ts}]"
                        content_text += f"  - {prefix} \"{text}\"\n"
                    elif isinstance(quote, str):
                        content_text += f"  - \"{quote}\"\n"
            if content_text_raw:
                content_text += f"Transcript/Content:\n{content_text_raw}\n"

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

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _get_source_key(self, item: Dict[str, Any]) -> str:
        """Get the source key for an item, with YouTube channel granularity."""
        source = item.get("source", "unknown")
        if source == "youtube" and item.get("channel_display"):
            return f"youtube:{item['channel_display']}"
        return source

    def _extract_levels_from_content(self, content_items: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Pre-scan content to extract specific levels, strikes, and dates."""
        extracted = {
            "price_levels": [],
            "option_strikes": [],
            "dates": [],
            "tickers": []
        }

        for item in content_items:
            text = str(item.get("content_text", "")) + " " + str(item.get("summary", ""))

            # Price levels (3-5 digit numbers)
            prices = re.findall(r'\b([1-9]\d{2,4}(?:\.\d{1,2})?)\b', text)
            extracted["price_levels"].extend(prices)

            # VIX levels
            vix_levels = re.findall(r'\bVIX\s*(?:at|to|above|below|@)?\s*(\d{1,2}(?:\.\d{1,2})?)\b', text, re.I)
            extracted["price_levels"].extend([f"VIX {v}" for v in vix_levels])

            # Option mentions
            options = re.findall(
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d+\s+(?:calls?|puts?))',
                text, re.I
            )
            extracted["option_strikes"].extend(options)

            # Strike format like "6000C" or "5900P"
            strike_format = re.findall(r'\b(\d{3,5}[CP])\b', text, re.I)
            extracted["option_strikes"].extend(strike_format)

            # Dates
            dates = re.findall(
                r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?(?:[,\s]+\d{4})?)',
                text, re.I
            )
            extracted["dates"].extend(dates)

            # Economic events
            events = re.findall(r'\b(FOMC|CPI|NFP|PCE|GDP|ISM)\b', text, re.I)
            for event in events:
                extracted["dates"].append(event.upper())

            # Tickers
            tickers = item.get("tickers", [])
            if isinstance(tickers, list):
                extracted["tickers"].extend(tickers)

        # Deduplicate and limit
        for key in extracted:
            extracted[key] = list(set(str(x).strip() for x in extracted[key] if x and str(x).strip()))
            extracted[key] = extracted[key][:25]

        return extracted

    def _generate_content_summaries(
        self,
        content_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate per-content-item summaries from existing analyzed data (no LLM call)."""
        summaries = []

        for item in content_items:
            content_id = item.get("id", item.get("content_id"))

            # Check if there's a pre-computed content summary
            analysis = item.get("analysis_result", {})
            if isinstance(analysis, str):
                try:
                    import json
                    analysis = json.loads(analysis)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse analysis_result for content {content_id}: {e}")
                    analysis = {}

            content_summary = analysis.get("content_summary", {})

            summary_entry = {
                "id": content_id,
                "source": item.get("source", "unknown"),
                "channel": item.get("channel_display"),
                "title": item.get("title", "Untitled"),
                "collected_at": item.get("collected_at", item.get("timestamp", "")),
                "content_type": item.get("type", item.get("content_type", "unknown")),
                "summary": content_summary.get("summary") or item.get("summary", ""),
                "themes": content_summary.get("themes") or item.get("themes", []),
                "key_points": content_summary.get("key_points", []),
                "tickers_mentioned": item.get("tickers", []),
                "sentiment": item.get("sentiment", "neutral")
            }

            summaries.append(summary_entry)

        return summaries

    def _empty_synthesis(self, time_window: str) -> Dict[str, Any]:
        """Return empty synthesis when no content available."""
        return {
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
            "catalyst_calendar": [],
            "source_breakdowns": {},
            "content_summaries": [],
            "time_window": time_window,
            "content_count": 0,
            "older_content_scanned": 0,
            "sources_included": [],
            "youtube_channels_included": [],
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
