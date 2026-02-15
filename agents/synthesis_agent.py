"""
Synthesis Agent

Generates research synthesis from collected content using a research assistant
persona. Uses a per-source analysis + merge architecture:

1. Analyze each source independently (full content, no truncation)
2. Merge source analyses into cross-source synthesis (confluence, conflicts, priorities)
3. Generate content summaries from existing analyzed data (no LLM call)
"""

import os
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from agents.base_agent import BaseAgent
from agents.config import MODEL_SYNTHESIS, TIMEOUT_SYNTHESIS, MAX_TRANSCRIPT_CHARS
from backend.utils.sanitization import wrap_content_for_prompt, sanitize_content_text

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

    # Source-specific analysis instructions
    SOURCE_INSTRUCTIONS = {
        "42macro": "Focus on: Darius Dale's macro framework signals, risk-reward regime, liquidity analysis, asset class positioning recommendations. Extract specific framework readings (e.g., GRID model, risk-reward quadrant).",
        "discord": "Focus on: Imran's specific trade structures (spreads, butterflies, calendars), entry/exit levels, position sizing, Greeks exposure, and tactical market reads. This is the ONLY source with actual trades.",
        "kt_technical": "Focus on: Elliott Wave counts for each instrument, specific support/resistance levels, wave completion targets, invalidation levels, and directional bias. Be precise with wave labels (e.g., 'wave 3 of C').",
        "substack": "Focus on: Thematic research narratives, longer-term macro/crypto analysis, structural market shifts, and emerging trends.",
    }

    YOUTUBE_CHANNEL_INSTRUCTIONS = {
        "Moonshots": "Focus on: AI breakthroughs, technology convergence, exponential trends, and abundance framework insights from Peter Diamandis and guests.",
        "Forward Guidance": "Focus on: Fed policy analysis, inflation dynamics, employment data interpretation, and macroeconomic outlook.",
        "Jordi Visser Labs": "Focus on: Information synthesis across markets, macro perspective shifts, and cross-asset relationship analysis.",
        "42 Macro": "Focus on: Video format of institutional macro research, risk-reward framework updates, and tactical positioning guidance.",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize Synthesis Agent with Opus model."""
        super().__init__(api_key=api_key, model=model or MODEL_SYNTHESIS, api_timeout=TIMEOUT_SYNTHESIS)
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
        Generate comprehensive research synthesis using per-source + merge architecture.

        Pipeline:
        1. Group content by source
        2. Analyze each source independently (full content, no truncation)
        3. Merge source analyses into cross-source synthesis
        4. Generate content summaries from existing data (no LLM call)

        Args:
            content_items: Recent content items (within time_window)
            older_content: Older content (7-30 days) for re-review scanning
            time_window: Time window being analyzed ("24h", "7d", "30d")
            focus_topic: Optional specific topic to focus on
            kt_symbol_data: KT Technical symbol-level data (wave counts, levels, bias)

        Returns:
            Unified synthesis dict with all sections (schema 5.0)
        """
        if not content_items:
            return self._empty_synthesis(time_window)

        logger.info(f"Generating synthesis for {len(content_items)} items over {time_window}")
        if older_content:
            logger.info(f"Including {len(older_content)} older items for re-review scanning")
        if kt_symbol_data:
            logger.info(f"Including KT Technical data for {len(kt_symbol_data)} symbols")

        # STEP 1: Group content by source
        source_groups = {}
        for item in content_items:
            source_key = self._get_source_key(item)
            source_groups.setdefault(source_key, []).append(item)

        logger.info(f"Grouped into {len(source_groups)} sources: {list(source_groups.keys())}")

        # STEP 2: Analyze each source independently
        source_analyses = {}
        youtube_channels = []

        for source_key, items in source_groups.items():
            if source_key.startswith("youtube:"):
                youtube_channels.append(source_key.split(":", 1)[1])

            try:
                analysis = self._analyze_source(
                    source_key=source_key,
                    items=items,
                    time_window=time_window,
                    focus_topic=focus_topic,
                    kt_symbol_data=kt_symbol_data
                )
                source_analyses[source_key] = analysis
                logger.info(f"Source analysis complete for {source_key}: {len(items)} items, bias={analysis.get('overall_bias', 'unknown')}")
            except Exception as e:
                logger.error(f"Source analysis failed for {source_key}: {e}")
                # Create degraded analysis so we can still merge
                source_analyses[source_key] = {
                    "summary": f"Analysis failed for {source_key}",
                    "key_insights": [],
                    "themes": [],
                    "overall_bias": "neutral",
                    "content_titles": [item.get("title", "Untitled") for item in items],
                    "key_views": [],
                    "catalysts_mentioned": [],
                    "tickers_discussed": [],
                    "notable_quotes": [],
                    "macro_context_contribution": "",
                    "degraded": True,
                    "degradation_reason": str(e)
                }

        # STEP 3: Merge source analyses into cross-source synthesis
        try:
            merge_result = self._merge_source_analyses(
                source_analyses=source_analyses,
                older_content=older_content,
                time_window=time_window,
                focus_topic=focus_topic,
                kt_symbol_data=kt_symbol_data
            )
        except Exception as e:
            logger.error(f"Merge failed: {e}")
            # Return partial result with source breakdowns but empty cross-source sections
            merge_result = {
                "executive_summary": {
                    "macro_context": "Synthesis merge failed — see individual source breakdowns.",
                    "source_highlights": {},
                    "synthesis_narrative": f"Error during merge: {str(e)}",
                    "key_takeaways": [],
                    "overall_tone": "uncertain",
                    "dominant_theme": None
                },
                "confluence_zones": [],
                "conflict_watch": [],
                "attention_priorities": [],
                "re_review_recommendations": [],
                "catalyst_calendar": [],
                "merge_error": str(e)
            }

        # Build source_breakdowns from per-source analyses (add weight + content_count)
        source_breakdowns = {}
        for source_key, analysis in source_analyses.items():
            if source_key.startswith("youtube:"):
                base_source = "youtube"
            else:
                base_source = source_key
            weight = self.SOURCE_WEIGHTS.get(base_source, 1.0)

            breakdown = {
                "summary": analysis.get("summary", ""),
                "key_insights": analysis.get("key_insights", []),
                "themes": analysis.get("themes", []),
                "overall_bias": analysis.get("overall_bias", "neutral"),
                "content_titles": analysis.get("content_titles", []),
                "weight": weight,
                "content_count": len(source_groups.get(source_key, []))
            }
            if analysis.get("degraded"):
                breakdown["degraded"] = True
                breakdown["degradation_reason"] = analysis.get("degradation_reason", "")
            source_breakdowns[source_key] = breakdown

        # STEP 4: Content summaries (no LLM call)
        content_summaries = self._generate_content_summaries(content_items)

        # Combine into unified result (schema 5.0)
        result = {
            "executive_summary": merge_result.get("executive_summary", {}),
            "confluence_zones": merge_result.get("confluence_zones", []),
            "conflict_watch": merge_result.get("conflict_watch", []),
            "attention_priorities": merge_result.get("attention_priorities", []),
            "catalyst_calendar": merge_result.get("catalyst_calendar", []),
            "re_review_recommendations": merge_result.get("re_review_recommendations", []),
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

        if merge_result.get("validation_passed") is False:
            result["validation_passed"] = False
            result["validation_error"] = merge_result.get("validation_error")

        if merge_result.get("merge_error"):
            result["merge_error"] = merge_result["merge_error"]

        logger.info(
            f"Generated synthesis: {len(merge_result.get('confluence_zones', []))} confluence zones, "
            f"{len(source_breakdowns)} source breakdowns, "
            f"{len(content_summaries)} content summaries, "
            f"{len(youtube_channels)} YouTube channels"
        )

        return result

    # =========================================================================
    # PER-SOURCE ANALYSIS
    # =========================================================================

    def _analyze_source(
        self,
        source_key: str,
        items: List[Dict[str, Any]],
        time_window: str,
        focus_topic: Optional[str] = None,
        kt_symbol_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze content from a single source. Full content, no truncation.

        Args:
            source_key: Source identifier (e.g., "42macro", "youtube:Forward Guidance")
            items: Content items from this source
            time_window: Time window being analyzed
            focus_topic: Optional topic filter
            kt_symbol_data: KT symbol data (injected for kt_technical source)

        Returns:
            Structured analysis dict for this source
        """
        prompt = self._build_source_analysis_prompt(
            source_key=source_key,
            items=items,
            time_window=time_window,
            focus_topic=focus_topic,
            kt_symbol_data=kt_symbol_data
        )

        # Source-specific system prompt
        if source_key.startswith("youtube:"):
            base_source = "youtube"
            channel = source_key.split(":", 1)[1]
            channel_instruction = self.YOUTUBE_CHANNEL_INSTRUCTIONS.get(channel, "Summarize key macro themes and insights.")
            system_prompt = f"You are analyzing investment research content from YouTube channel '{channel}'. {channel_instruction} Be specific and include key data points, levels, and quotes."
        else:
            base_source = source_key
            source_instruction = self.SOURCE_INSTRUCTIONS.get(source_key, "Summarize key themes and insights from this source.")
            system_prompt = f"You are analyzing investment research content from {source_key}. {source_instruction} Be specific and include key data points, levels, and quotes."

        result = self.call_claude(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=6000,
            temperature=0.2,
            expect_json=True
        )

        return result

    def _build_source_analysis_prompt(
        self,
        source_key: str,
        items: List[Dict[str, Any]],
        time_window: str,
        focus_topic: Optional[str] = None,
        kt_symbol_data: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Build prompt for analyzing a single source's content.
        Includes FULL content text — no truncation.
        """
        content_section = ""
        for item in items:
            title = item.get("title", "Untitled")
            content_type = item.get("type", item.get("content_type", "unknown"))
            timestamp = item.get("timestamp", item.get("collected_at", ""))
            summary = str(item.get("summary", ""))
            content_text_raw = str(item.get("content_text", ""))
            themes = item.get("themes", [])
            sentiment = item.get("sentiment", "")
            key_quotes = item.get("key_quotes", [])

            content_section += f"\n### {title} ({content_type})\n"
            if timestamp:
                content_section += f"Time: {timestamp}\n"
            if themes:
                content_section += f"Pre-analyzed themes: {', '.join(themes[:5])}\n"
            if sentiment:
                content_section += f"Pre-analyzed sentiment: {sentiment}\n"
            if summary:
                content_section += f"Pre-analyzed summary: {summary}\n"
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
            # Intelligent transcript handling: use summary for long content, wrap for injection protection
            analyzed_summary = str(item.get("analyzed_summary", ""))
            if analyzed_summary and len(content_text_raw) > MAX_TRANSCRIPT_CHARS:
                content_section += f"\n[Pre-analyzed Summary]:\n{analyzed_summary}\n"
                if themes:
                    content_section += f"Key Themes: {', '.join(themes[:5])}\n"
                content_section += f"[Note: Full transcript ({len(content_text_raw)} chars) truncated. Analysis above covers key points.]\n"
            elif content_text_raw:
                safe_content = sanitize_content_text(content_text_raw)
                wrapped = wrap_content_for_prompt(safe_content, max_chars=MAX_TRANSCRIPT_CHARS)
                content_section += f"\nFull Content/Transcript:\n{wrapped}\n"

        # KT symbol data injection for kt_technical source
        kt_section = ""
        if source_key == "kt_technical" and kt_symbol_data:
            kt_section = "\n## STRUCTURED SYMBOL DATA (from database)\n"
            for sym_data in kt_symbol_data:
                symbol = sym_data.get("symbol", "UNKNOWN")
                kt_section += f"### {symbol}\n"
                for field in ["wave_position", "wave_direction", "wave_phase", "bias",
                              "primary_target", "primary_support", "invalidation", "notes", "last_updated"]:
                    val = sym_data.get(field)
                    if val:
                        kt_section += f"- {field.replace('_', ' ').title()}: {val}\n"
                kt_section += "\n"

        focus_instruction = ""
        if focus_topic:
            focus_instruction = f"\nFOCUS: Pay particular attention to content related to: {focus_topic}\n"

        return f"""Analyze the following content from {source_key} collected over the past {time_window}.
{focus_instruction}
## CONTENT
{content_section}
{kt_section}
## REQUIRED OUTPUT (JSON)

Produce a thorough analysis of this source's content:

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
  "content_titles": ["Title 1", "Title 2"],
  "key_views": [
    {{
      "topic": "What this view is about (e.g., 'SPX direction', 'Fed policy', 'Vol regime')",
      "view": "The source's specific view on this topic",
      "conviction": "high|medium|low",
      "levels": ["Specific price levels if mentioned"],
      "timeframe": "immediate|short-term|medium-term|long-term"
    }}
  ],
  "catalysts_mentioned": [
    {{
      "event": "Event name",
      "date": "Date if mentioned or null",
      "impact_view": "What this source thinks about the event's impact"
    }}
  ],
  "tickers_discussed": ["SPX", "QQQ"],
  "notable_quotes": [
    "Direct quote that captures a key view"
  ],
  "macro_context_contribution": "1-2 sentences on what this source adds to the macro picture"
}}

Be SPECIFIC. Include price levels, dates, and key data points mentioned in the content.
RESPOND WITH VALID JSON ONLY."""

    # =========================================================================
    # MERGE SOURCE ANALYSES
    # =========================================================================

    def _merge_source_analyses(
        self,
        source_analyses: Dict[str, Dict[str, Any]],
        older_content: Optional[List[Dict[str, Any]]] = None,
        time_window: str = "24h",
        focus_topic: Optional[str] = None,
        kt_symbol_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Merge per-source analyses into cross-source synthesis.

        Receives structured per-source summaries (NOT raw content — compact token usage)
        and identifies confluence, conflicts, and priorities.

        Args:
            source_analyses: Dict of source_key -> analysis dict
            older_content: Older content for re-review recommendations
            time_window: Time window
            focus_topic: Optional topic filter
            kt_symbol_data: KT symbol data for level references

        Returns:
            Merged synthesis with all cross-source sections
        """
        prompt = self._build_merge_prompt(
            source_analyses=source_analyses,
            older_content=older_content,
            time_window=time_window,
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
            logger.warning(f"Merge schema validation failed: {e}, continuing with partial response")
            response["validation_passed"] = False
            response["validation_error"] = str(e)

        # Validate and clamp response values
        response = self._validate_merge_response(response)

        # Surface degradation warnings
        degraded_sources = [key for key, analysis in source_analyses.items() if analysis.get("degraded")]
        if degraded_sources:
            degradation_warning = f"WARNING: Analysis was incomplete for: {', '.join(degraded_sources)}. Findings may be less reliable."
            if "executive_summary" in response:
                exec_summary = response["executive_summary"]
                if isinstance(exec_summary, dict):
                    exec_summary["degradation_warning"] = degradation_warning
                elif isinstance(exec_summary, str):
                    response["executive_summary"] = f"[{degradation_warning}]\n\n{exec_summary}"

        return response

    def _build_merge_prompt(
        self,
        source_analyses: Dict[str, Dict[str, Any]],
        older_content: Optional[List[Dict[str, Any]]] = None,
        time_window: str = "24h",
        focus_topic: Optional[str] = None,
        kt_symbol_data: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Build the merge prompt from per-source analysis summaries.
        Labels each source with its weight for weighted lean calculations.
        """
        # Build per-source summary sections
        source_section = ""
        for source_key, analysis in source_analyses.items():
            if source_key.startswith("youtube:"):
                base_source = "youtube"
                channel = source_key.split(":", 1)[1]
                weight = self.SOURCE_WEIGHTS.get(base_source, 1.0)
                source_section += f"\n### YOUTUBE - {channel} (Weight: {weight}x)\n"
            else:
                weight = self.SOURCE_WEIGHTS.get(source_key, 1.0)
                source_section += f"\n### {source_key.upper()} (Weight: {weight}x)\n"

            if analysis.get("degraded"):
                source_section += f"[WARNING] Analysis degraded: {analysis.get('degradation_reason', 'unknown')}\n"

            source_section += f"**Summary**: {analysis.get('summary', 'No summary')}\n"
            source_section += f"**Bias**: {analysis.get('overall_bias', 'neutral')}\n"

            key_insights = analysis.get("key_insights", [])
            if key_insights:
                source_section += "**Key Insights**:\n"
                for insight in key_insights[:5]:
                    source_section += f"  - {insight}\n"

            themes = analysis.get("themes", [])
            if themes:
                source_section += f"**Themes**: {', '.join(themes)}\n"

            key_views = analysis.get("key_views", [])
            if key_views:
                source_section += "**Key Views**:\n"
                for view in key_views[:5]:
                    if isinstance(view, dict):
                        topic = view.get("topic", "")
                        view_text = view.get("view", "")
                        conviction = view.get("conviction", "")
                        levels = view.get("levels", [])
                        tf = view.get("timeframe", "")
                        source_section += f"  - {topic}: {view_text}"
                        if conviction:
                            source_section += f" (conviction: {conviction})"
                        if levels:
                            source_section += f" [levels: {', '.join(str(l) for l in levels)}]"
                        if tf:
                            source_section += f" [{tf}]"
                        source_section += "\n"

            catalysts = analysis.get("catalysts_mentioned", [])
            if catalysts:
                source_section += "**Catalysts Mentioned**:\n"
                for cat in catalysts[:3]:
                    if isinstance(cat, dict):
                        source_section += f"  - {cat.get('event', '')}: {cat.get('impact_view', '')} ({cat.get('date', 'TBD')})\n"

            tickers = analysis.get("tickers_discussed", [])
            if tickers:
                source_section += f"**Tickers**: {', '.join(tickers)}\n"

            quotes = analysis.get("notable_quotes", [])
            if quotes:
                source_section += "**Notable Quotes**:\n"
                for q in quotes[:3]:
                    source_section += f'  - "{q}"\n'

            macro_contrib = analysis.get("macro_context_contribution", "")
            if macro_contrib:
                source_section += f"**Macro Context**: {macro_contrib}\n"

            source_section += "\n"

        # Older content section (compact form — title, date, themes, summary only)
        older_section = ""
        if older_content:
            older_section = "\n## OLDER CONTENT (7-30 days ago) — scan for re-review candidates\n"
            older_by_source = {}
            for item in older_content:
                display_key = self._get_source_key(item)
                older_by_source.setdefault(display_key, []).append(item)

            for src_key, items in older_by_source.items():
                if src_key.startswith("youtube:"):
                    channel_name = src_key.split(":", 1)[1]
                    older_section += f"\n### YOUTUBE - {channel_name} (older)\n"
                else:
                    older_section += f"\n### {src_key.upper()} (older)\n"
                for item in items:
                    title = item.get("title", "Untitled")
                    timestamp = item.get("timestamp", item.get("collected_at", ""))
                    themes = item.get("themes", [])
                    summary = str(item.get("summary", ""))
                    older_section += f"- **{title}** ({timestamp}): {', '.join(themes[:3])}. {summary}\n"

        # KT symbol data reference
        kt_section = ""
        if kt_symbol_data:
            kt_section = "\n## KT TECHNICAL SYMBOL-LEVEL DATA (structured)\n"
            for sym_data in kt_symbol_data:
                symbol = sym_data.get("symbol", "UNKNOWN")
                kt_section += f"- {symbol}: "
                parts = []
                if sym_data.get("wave_position"):
                    parts.append(f"wave={sym_data['wave_position']}")
                if sym_data.get("bias"):
                    parts.append(f"bias={sym_data['bias']}")
                if sym_data.get("primary_target"):
                    parts.append(f"target={sym_data['primary_target']}")
                if sym_data.get("primary_support"):
                    parts.append(f"support={sym_data['primary_support']}")
                if sym_data.get("invalidation"):
                    parts.append(f"invalidation={sym_data['invalidation']}")
                kt_section += ", ".join(parts) + "\n"

        # Extract levels for reference
        all_tickers = []
        for analysis in source_analyses.values():
            all_tickers.extend(analysis.get("tickers_discussed", []))
        all_tickers = list(set(all_tickers))

        focus_instruction = ""
        if focus_topic:
            focus_instruction = f"\n\nFOCUS: Pay particular attention to content related to: {focus_topic}\n"

        prompt = f"""You have received per-source analysis summaries from {len(source_analyses)} research sources covering the past {time_window}.

Your job: MERGE these into a unified cross-source synthesis. Identify where sources ALIGN (confluence), DISAGREE (conflicts), and what deserves ATTENTION.
{focus_instruction}
## PER-SOURCE ANALYSES
{source_section}
{older_section}
{kt_section}
## TICKERS DISCUSSED ACROSS SOURCES
{', '.join(all_tickers[:20]) or 'None'}

## REQUIRED OUTPUT (JSON)

### 1. executive_summary (required object — COMPREHENSIVE FORMAT)
{{
  "macro_context": "1-2 sentences setting the stage for what's happening in markets right now.",

  "source_highlights": {{
    "42macro": "2-3 sentences on 42Macro's current stance, or null if no content",
    "discord": "2-3 sentences on Discord's current focus, or null if no content",
    "kt_technical": "2-3 sentences on KT Technical's view, or null if no content",
    "youtube_moonshots": "1-2 sentences on Moonshots content if present, otherwise null",
    "youtube_forward_guidance": "1-2 sentences on Forward Guidance content if present, otherwise null",
    "youtube_jordi_visser": "1-2 sentences on Jordi Visser Labs content if present, otherwise null",
    "youtube_42macro": "1-2 sentences on 42 Macro video content if present, otherwise null",
    "substack": "1-2 sentences if relevant content, otherwise null"
  }},

  "synthesis_narrative": "2-3 PARAGRAPHS connecting the dots across all sources:\\n\\nParagraph 1: Where sources ALIGN (confluence).\\n\\nParagraph 2: Where sources DIFFER and what that means.\\n\\nParagraph 3: What deserves attention and why.",

  "key_takeaways": [
    "Takeaway 1: Most important insight (be specific with levels/dates)",
    "Takeaway 2: Second most important insight",
    "Takeaway 3: Third insight",
    "Takeaway 4: Optional",
    "Takeaway 5: Optional"
  ],

  "overall_tone": "bullish|bearish|neutral|cautious|uncertain|transitioning",
  "dominant_theme": "The single most important theme across sources"
}}

### 2. confluence_zones (required array)
Where do independent sources ALIGN? Use source weights for confluence_strength.
{{
  "theme": "The theme/view where sources align",
  "confluence_strength": 0.0-1.0,
  "sources_aligned": [{{"source": "name", "view": "1 sentence"}}],
  "sources_contrary": [{{"source": "name", "view": "contrary view if any"}}],
  "relevant_levels": ["Specific price levels"],
  "related_catalyst": "Upcoming event or null"
}}

### 3. conflict_watch (required array)
Where do sources DISAGREE?
{{
  "topic": "Topic with conflicting views",
  "status": "active_conflict|developing|monitoring",
  "bull_case": {{"view": "bullish argument", "sources": ["source1"]}},
  "bear_case": {{"view": "bearish argument", "sources": ["source2"]}},
  "resolution_trigger": "What would resolve this",
  "weighted_lean": "slight_bull|slight_bear|neutral (use source weights)",
  "user_action": "What to monitor"
}}

### 4. attention_priorities (required array, MAX 5)
Ranked by importance. Use source weights to determine ranking.
{{
  "rank": 1-5,
  "focus_area": "What to focus on",
  "why": "Why this deserves attention (1-2 sentences)",
  "sources_discussing": ["sources"],
  "time_sensitivity": "immediate|high|medium|low"
}}

### 5. re_review_recommendations (required array, 3-5 items)
Older content that is NOW more relevant due to current conditions.
{{
  "source": "source_name",
  "content_date": "approximate date",
  "title": "content title",
  "why_relevant_now": "2-3 sentences",
  "themes_mentioned": ["theme1"],
  "relevance_trigger": "catalyst_approaching|level_being_tested|scenario_playing_out|conflict_resolving"
}}

### 6. catalyst_calendar (required array)
Upcoming events with source perspectives.
{{
  "date": "YYYY-MM-DD",
  "event": "Event name",
  "impact": "high|medium|low",
  "source_perspectives": [{{"source": "name", "view": "view"}}],
  "themes_affected": ["theme"],
  "pre_event_review": "Content to review before this event, or null"
}}

Economic calendar patterns: NFP is first Friday of month, CPI typically 10th-13th, FOMC ~8x/year, Quad Witch 3rd Friday of Mar/Jun/Sep/Dec.

RESPOND WITH VALID JSON ONLY."""

        return prompt

    def _validate_merge_response(self, response: dict) -> dict:
        """Validate and sanitize the merge response values."""
        # Validate confluence_strength is 0.0-1.0
        for zone in response.get("confluence_zones", []):
            if isinstance(zone, dict) and "confluence_strength" in zone:
                score = zone["confluence_strength"]
                if isinstance(score, (int, float)):
                    zone["confluence_strength"] = max(0.0, min(1.0, float(score)))
                else:
                    zone["confluence_strength"] = 0.5

        # Validate overall_tone is a valid enum
        exec_summary = response.get("executive_summary", {})
        if isinstance(exec_summary, dict):
            valid_tones = ["bullish", "bearish", "neutral", "mixed", "cautious",
                           "cautiously_bullish", "cautiously_bearish", "uncertain", "transitioning"]
            if exec_summary.get("overall_tone") not in valid_tones:
                logger.warning(f"Invalid overall_tone '{exec_summary.get('overall_tone')}', defaulting to 'neutral'")
                exec_summary["overall_tone"] = "neutral"

        # Validate arrays are actually arrays
        array_fields = ["confluence_zones", "conflict_watch", "attention_priorities",
                        "re_review_recommendations", "catalyst_calendar"]
        for field in array_fields:
            if field in response and not isinstance(response[field], list):
                logger.warning(f"Expected array for {field}, got {type(response[field])}")
                response[field] = []

        return response

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
