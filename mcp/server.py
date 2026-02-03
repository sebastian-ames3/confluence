#!/usr/bin/env python3
"""
Confluence Research Hub MCP Server

Provides Claude Desktop access to your research synthesis and content.

Usage:
    python server.py          # Run as HTTP server (for Claude Desktop remote MCP)
    python server.py --stdio  # Run as stdio server (for local MCP)

The HTTP server runs at http://localhost:8765/sse

Requires environment variables:
    CONFLUENCE_API_URL - Base URL of Confluence Hub API
    CONFLUENCE_USERNAME - API username
    CONFLUENCE_PASSWORD - API password
"""

import asyncio
import json
import logging
import sys
import os
from typing import Optional

from mcp.server import Server
from mcp.types import Tool, TextContent

from confluence_client import (
    ConfluenceClient,
    extract_confluence_zones,
    extract_conflicts,
    extract_attention_priorities,
    extract_source_breakdowns,
    extract_catalyst_calendar,
    extract_re_review_recommendations,
    extract_executive_summary
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("confluence-mcp")

# Initialize the MCP server
server = Server("confluence-research")

# Global client (initialized on first use)
_client: Optional[ConfluenceClient] = None


def get_client() -> ConfluenceClient:
    """Get or create the Confluence client."""
    global _client
    if _client is None:
        _client = ConfluenceClient()
    return _client


# =============================================================================
# MCP Tools
# =============================================================================

@server.list_tools()
async def list_tools():
    """List all available tools."""
    return [
        Tool(
            name="get_latest_synthesis",
            description="""Get the latest research synthesis from Confluence Hub.

Returns the full synthesis including:
- Executive summary with macro context and key takeaways
- Confluence zones (where sources align)
- Conflict watch (where sources disagree)
- Attention priorities (what to focus on)
- Catalyst calendar (upcoming events)
- Source breakdowns (per-source detailed summaries, YouTube channels shown separately)
- Content summaries (per-content item summaries)

Use this for a comprehensive overview of your research.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_executive_summary",
            description="""Get just the executive summary from the latest synthesis.

Returns:
- Narrative summary of what your sources are saying
- Overall tone (cautious, constructive, mixed, uncertain)
- Dominant theme

Use this for a quick overview.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_confluence_zones",
            description="""Get themes where multiple research sources align.

Returns confluence zones showing:
- Theme name
- Confluence strength (0-100%)
- Which sources align and their views
- Any contrary views
- Related catalyst

Use this to understand where your research sources agree.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_conflicts",
            description="""Get active conflicts/disagreements between research sources.

Returns conflicts showing:
- Topic of disagreement
- Bull case (view and sources)
- Bear case (view and sources)
- Resolution trigger (what would resolve it)
- Weighted lean (which side has more weight)

Use this to understand where your sources disagree.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_attention_priorities",
            description="""Get the ranked list of what deserves focus this week.

Returns priorities (ranked 1-5) with:
- Focus area (instrument, theme, or event)
- Why it matters now
- Time sensitivity (immediate, high, medium, low)
- Which sources are discussing it

Use this to know what to pay attention to.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_source_stance",
            description="""Get what a specific research source is currently saying.

Available sources:
- discord (Imran's options flow and trades)
- 42macro (institutional macro research)
- kt_technical (Elliott Wave analysis)
- substack (thematic research)

YouTube channels (PRD-040 granularity):
- youtube:42 Macro (Darius Dale's video content)
- youtube:Forward Guidance (macro/crypto interviews)
- youtube:Jordi Visser Labs (Weiss Multi-Strategy)
- youtube:Moonshots (growth/momentum)

You can search by partial name (e.g., "forward" matches "youtube:Forward Guidance").

Returns:
- Narrative of what the source is thinking
- Key insights and themes
- Overall bias (bullish, bearish, cautious, neutral, mixed)
- Content count""",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source name (discord, 42macro, kt_technical, substack) or YouTube channel (youtube:Channel Name or partial match like 'forward')"
                    }
                },
                "required": ["source"]
            }
        ),
        Tool(
            name="get_catalyst_calendar",
            description="""Get upcoming market catalysts and what sources say about them.

Returns events with:
- Date
- Event name (NFP, CPI, FOMC, etc.)
- Impact level (high, medium, low)
- What each source says about it
- Pre-event content to review

Use this to prepare for upcoming market events.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_re_review_recommendations",
            description="""Get older research content that's now highly relevant.

Returns recommendations with:
- Source and approximate date
- Content title/description
- Why it's relevant NOW
- Relevance trigger (catalyst approaching, level being tested, scenario playing out)

Use this to find older research worth revisiting.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_research",
            description="""Search across collected research content for specific topics.

Args:
- query: What to search for (e.g., "VIX", "Bitcoin", "FOMC", "volatility")
- source: Optional - filter by source (discord, 42macro, kt_technical, youtube, substack)
- days: How many days back to search (default 7)

Returns matching content with source, date, themes, and summary.

Use this to find specific research on a topic.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (e.g., VIX, Bitcoin, FOMC)"
                    },
                    "source": {
                        "type": "string",
                        "description": "Optional: filter by source name"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Days to search back (default 7)"
                    }
                },
                "required": ["query"]
            }
        ),
        # PRD-024: Theme Tracking Tools
        Tool(
            name="get_themes",
            description="""Get tracked investment themes from your research.

Themes are extracted from synthesis and tracked over time.
Each theme has:
- Name and description
- Status lifecycle: emerging → active → evolved → dormant
- Source evidence (what each source says about it)
- Related catalysts
- First mentioned date and last updated

Args:
- status: Optional - filter by status (emerging, active, evolved, dormant)

Use this to understand the major themes across your research.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Optional: filter by status (emerging, active, evolved, dormant)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_active_themes",
            description="""Get currently active investment themes (emerging + active).

Returns themes that are currently relevant:
- Emerging: New themes mentioned by 1-2 sources
- Active: Established themes with multiple sources

Excludes evolved (superseded) and dormant (no longer relevant) themes.

Use this for a quick view of what themes matter right now.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_theme_detail",
            description="""Get detailed information about a specific theme.

Args:
- theme_id: The numeric ID of the theme

Returns full theme details including:
- Complete source evidence (what each source says)
- All related catalysts
- Evolution history (if evolved from another theme)
- Timeline of updates

Use this to deep-dive into a specific theme.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "theme_id": {
                        "type": "integer",
                        "description": "Theme ID number"
                    }
                },
                "required": ["theme_id"]
            }
        ),
        Tool(
            name="get_themes_summary",
            description="""Get summary statistics about tracked themes.

Returns:
- Total theme count
- Count by status (emerging, active, evolved, dormant)
- Recent theme activity

Use this for a quick overview of theme tracking status.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_symbol_analysis",
            description="""Get complete analysis for a tracked symbol (PRD-039).

Returns KT Technical view (wave count, levels, bias),
Discord view (quadrant, IV regime, strategy),
and confluence assessment.

Tracked symbols: SPX, QQQ, IWM, BTC, SMH, TSLA, NVDA, GOOGL, AAPL, MSFT, AMZN

Use this to get the full picture for a specific symbol.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Symbol ticker (e.g., GOOGL, SPX, QQQ)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_symbol_levels",
            description="""Get all active price levels for a symbol (PRD-039).

Returns support, resistance, targets, invalidation levels
with context snippets and direction vectors.

Optionally filter by source (kt_technical or discord).

Use this to see specific price levels for trading.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Symbol ticker"
                    },
                    "source": {
                        "type": "string",
                        "description": "Optional: filter by source (kt_technical or discord)"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_confluence_opportunities",
            description="""Get symbols where KT Technical and Discord are aligned (PRD-039).

Returns symbols with high confluence scores (>0.7),
including suggested trade setups.

Use this to find high-conviction setups where both sources agree.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_trade_setup",
            description="""Generate a trade setup for a symbol based on current state (PRD-039).

Combines KT Technical levels with Discord positioning
to suggest entry, stop, target, and structure.

Only works when sources are directionally aligned.

Use this to brainstorm specific trade ideas.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Symbol ticker"
                    }
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_content_detail",
            description="""Get the full content/transcript for a specific content item by ID.

Use this AFTER search_research to drill into a specific piece of content.
search_research returns IDs and short snippets; this returns the complete text.

Returns:
- Full content_text (complete transcript, no truncation)
- content_length (character count)
- Parsed analysis: summary, key_quotes, catalysts, falsification_criteria
- Metadata: source, title, url, collected_at, content_type
- Denormalized: themes, tickers, sentiment, conviction

Example workflow:
1. search_research(query="VIX") -> find item with id=42
2. get_content_detail(content_id=42) -> read the full transcript""",
            inputSchema={
                "type": "object",
                "properties": {
                    "content_id": {
                        "type": "integer",
                        "description": "Content ID (from search_research results)"
                    }
                },
                "required": ["content_id"]
            }
        ),
        # PRD-044: Synthesis Quality Tool
        Tool(
            name="get_synthesis_quality",
            description="""Get quality evaluation for the latest synthesis (PRD-044).

Returns AI-evaluated quality metrics:
- Overall score (0-100) and letter grade (A+ to F)
- Seven domain criteria scores (0-3 each):
  * Confluence detection (20% weight) - Are cross-source alignments identified?
  * Evidence preservation (15%) - Do themes have supporting data points?
  * Source attribution (15%) - Can insights be traced to specific sources?
  * YouTube channel granularity (15%) - Are channels named individually?
  * Nuance retention (15%) - Are conflicting views within sources captured?
  * Actionability (10%) - Are there specific levels, triggers, timeframes?
  * Theme continuity (10%) - References theme evolution over time?

Also returns:
- Flags: Issues where criteria scored 1 or below
- Prompt suggestions: Specific improvements for future synthesis

Use this to understand synthesis quality and identify improvement areas.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "synthesis_id": {
                        "type": "integer",
                        "description": "Optional: specific synthesis ID. Defaults to latest."
                    }
                },
                "required": []
            }
        ),
        # PRD-051: Individual Content Access Tools
        Tool(
            name="list_recent_content",
            description="""List recent videos, PDFs, and articles from your research sources.

Use this to browse what content has been collected recently, then use
get_content_detail to dive into a specific video or document.

Args:
- source: Optional filter (youtube, 42macro, discord, kt_technical, substack)
- content_type: Optional filter (video, pdf, text, image)
- days: Days to look back (default 7)
- limit: Max items to return (default 20)

Returns list of content items with:
- id: Use this with get_content_detail to get full content
- title: Video/document title
- source: Which source (youtube, discord, etc.)
- channel: YouTube channel name if applicable
- type: Content type (video, pdf, etc.)
- date: When collected
- summary: Brief summary
- themes: Extracted themes
- has_transcript: Whether full transcript is available

Example: "Show me recent Forward Guidance videos" → list_recent_content(source="youtube", content_type="video")""",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Filter by source: youtube, 42macro, discord, kt_technical, substack"
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Filter by type: video, pdf, text, image"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Days to look back (default 7)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max items to return (default 20)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_content_detail",
            description="""Get full details for a specific video, PDF, or article.

Use list_recent_content first to find content, then use this tool
with the content ID to get the full transcript/text and analysis.

Args:
- content_id: The numeric ID from list_recent_content

Returns:
- Full content text (transcript for videos, full text for PDFs/articles)
- Complete AI analysis (summary, key points, themes, sentiment)
- Metadata (channel, duration, views for videos)
- Trade ideas and market implications extracted by AI

Example conversation:
User: "What did Forward Guidance say about Bitcoin?"
Assistant: [uses list_recent_content to find FG videos mentioning Bitcoin]
Assistant: [uses get_content_detail to get full transcript of relevant video]
Assistant: "In the January 15th episode, Jack discussed..."

This enables detailed discussion of individual pieces of research content.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "content_id": {
                        "type": "integer",
                        "description": "Content ID from list_recent_content"
                    }
                },
                "required": ["content_id"]
            }
        ),
        # New tools: synthesis history, quality, health, theme evolution
        Tool(
            name="get_synthesis_history",
            description="""Get a list of recent synthesis runs.

Returns synthesis metadata (ID, timestamp, time window, content count)
for browsing past syntheses. Use get_synthesis_by_id to fetch full detail.

Args:
- limit: Number of results (1-50, default 10)
- offset: Pagination offset (default 0)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of results (1-50, default 10)"
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Pagination offset (default 0)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_synthesis_by_id",
            description="""Get a specific past synthesis by its ID.

Returns the full synthesis document including executive summary,
confluence zones, conflicts, attention priorities, and source breakdowns.

Use get_synthesis_history to find synthesis IDs.

Args:
- synthesis_id: The numeric synthesis ID (required)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "synthesis_id": {
                        "type": "integer",
                        "description": "Synthesis ID (from get_synthesis_history)"
                    }
                },
                "required": ["synthesis_id"]
            }
        ),
        Tool(
            name="get_quality_trends",
            description="""Get quality score trends over a time period.

Shows how synthesis quality has changed over time, including
overall scores, per-criterion trends, and grade distribution.

Args:
- days: Number of days to look back (1-90, default 30)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Days to look back (1-90, default 30)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_quality_flagged",
            description="""Get syntheses that have quality flags/issues.

Returns syntheses where one or more quality criteria scored poorly,
including the specific flags and details about what went wrong.

Args:
- limit: Number of results (default 10)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of results (default 10)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_system_health",
            description="""Get health status for all data sources.

Returns per-source health including:
- Last collection time
- Collection success/failure counts
- Data freshness and staleness warnings
- Overall system status

Use this to check if data collection is running properly.""",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_active_alerts",
            description="""Get active system alerts.

Returns alerts about issues like stale data, failed collections,
or degraded service. Alerts have severity levels and timestamps.

Args:
- include_acknowledged: Include already-acknowledged alerts (default false)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_acknowledged": {
                        "type": "boolean",
                        "description": "Include acknowledged alerts (default false)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_theme_evolution",
            description="""Get historical evolution data for a specific theme.

Shows how a theme has changed over time including conviction shifts,
source mentions, and status transitions.

Args:
- theme_id: The numeric theme ID (required)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "theme_id": {
                        "type": "integer",
                        "description": "Theme ID number"
                    }
                },
                "required": ["theme_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    import time
    start_time = time.time()

    # PRD-049: Structured logging for tool calls
    logger.info(f"[MCP] Tool '{name}' called with args: {arguments}")

    try:
        client = get_client()

        if name == "get_latest_synthesis":
            synthesis = client.get_latest_synthesis()
            return [TextContent(
                type="text",
                text=json.dumps(synthesis, indent=2)
            )]

        elif name == "get_executive_summary":
            synthesis = client.get_latest_synthesis()
            summary = extract_executive_summary(synthesis)
            summary["time_window"] = synthesis.get("time_window")
            summary["content_count"] = synthesis.get("content_count")
            summary["generated_at"] = synthesis.get("generated_at")
            return [TextContent(
                type="text",
                text=json.dumps(summary, indent=2)
            )]

        elif name == "get_confluence_zones":
            synthesis = client.get_latest_synthesis()
            zones = extract_confluence_zones(synthesis)
            return [TextContent(
                type="text",
                text=json.dumps(zones, indent=2)
            )]

        elif name == "get_conflicts":
            synthesis = client.get_latest_synthesis()
            conflicts = extract_conflicts(synthesis)
            return [TextContent(
                type="text",
                text=json.dumps(conflicts, indent=2)
            )]

        elif name == "get_attention_priorities":
            synthesis = client.get_latest_synthesis()
            priorities = extract_attention_priorities(synthesis)
            return [TextContent(
                type="text",
                text=json.dumps(priorities, indent=2)
            )]

        elif name == "get_source_stance":
            source = arguments.get("source", "").lower()
            synthesis = client.get_latest_synthesis()

            breakdowns = extract_source_breakdowns(synthesis)

            if not breakdowns:
                return [TextContent(
                    type="text",
                    text="No source breakdown data available in the current synthesis."
                )]

            # Find matching source (case-insensitive, supports partial matching)
            matched_data = None
            matched_key = None

            for key, value in breakdowns.items():
                if not isinstance(value, dict):
                    continue
                key_lower = key.lower() if isinstance(key, str) else ""
                # Exact match
                if key_lower == source:
                    matched_data = value
                    matched_key = key
                    break
                # Partial match (e.g., "forward" matches "youtube:Forward Guidance")
                if source in key_lower:
                    matched_data = value
                    matched_key = key
                    break

            if matched_data:
                display_name = matched_key.split(":", 1)[1] if ":" in matched_key else matched_key
                output = {
                    "source": matched_key,
                    "display_name": display_name,
                    "narrative": matched_data.get("summary", ""),
                    "key_insights": matched_data.get("key_insights", []),
                    "themes": matched_data.get("themes", []),
                    "overall_bias": matched_data.get("overall_bias", "neutral"),
                    "content_count": matched_data.get("content_count", 0)
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(output, indent=2)
                )]
            else:
                available = list(breakdowns.keys())
                return [TextContent(
                    type="text",
                    text=f"Source '{source}' not found. Available sources: {available}"
                )]

        elif name == "get_catalyst_calendar":
            synthesis = client.get_latest_synthesis()
            calendar = extract_catalyst_calendar(synthesis)
            return [TextContent(
                type="text",
                text=json.dumps(calendar, indent=2)
            )]

        elif name == "get_re_review_recommendations":
            synthesis = client.get_latest_synthesis()
            recommendations = extract_re_review_recommendations(synthesis)
            return [TextContent(
                type="text",
                text=json.dumps(recommendations, indent=2)
            )]

        elif name == "search_research":
            query = arguments.get("query", "")
            source = arguments.get("source")
            days = arguments.get("days", 7)

            results = client.search_content(query, source=source, days=days)
            return [TextContent(
                type="text",
                text=json.dumps(results, indent=2)
            )]

        elif name == "get_content_detail":
            content_id = arguments.get("content_id")
            if content_id is None:
                return [TextContent(
                    type="text",
                    text="Error: content_id is required"
                )]
            try:
                content_id = int(content_id)
                detail = client.get_content_detail(content_id)
                return [TextContent(
                    type="text",
                    text=json.dumps(detail, indent=2)
                )]
            except ValueError:
                return [TextContent(
                    type="text",
                    text=f"Error: content_id must be an integer, got '{arguments.get('content_id')}'"
                )]
            except Exception as e:
                logger.error(f"get_content_detail failed for id {content_id}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching content {content_id}: {str(e)}"
                )]

        # PRD-024: Theme Tracking Tools
        # PRD-049: Added try/catch and explicit None validation
        elif name == "get_themes":
            try:
                status = arguments.get("status")
                themes = client.get_themes(status=status)
                return [TextContent(
                    type="text",
                    text=json.dumps(themes, indent=2)
                )]
            except Exception as e:
                logger.error(f"get_themes failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching themes: {str(e)}"
                )]

        elif name == "get_active_themes":
            try:
                themes = client.get_active_themes()
                return [TextContent(
                    type="text",
                    text=json.dumps(themes, indent=2)
                )]
            except Exception as e:
                logger.error(f"get_active_themes failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching active themes: {str(e)}"
                )]

        elif name == "get_theme_detail":
            theme_id = arguments.get("theme_id")
            # PRD-049: Use explicit None check (0 is valid but falsy)
            if theme_id is None:
                return [TextContent(
                    type="text",
                    text="Error: theme_id is required"
                )]
            try:
                # Ensure theme_id is an integer
                theme_id = int(theme_id)
                theme = client.get_theme(theme_id)
                return [TextContent(
                    type="text",
                    text=json.dumps(theme, indent=2)
                )]
            except ValueError:
                return [TextContent(
                    type="text",
                    text=f"Error: theme_id must be an integer, got '{theme_id}'"
                )]
            except Exception as e:
                logger.error(f"get_theme_detail failed for id {theme_id}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching theme {theme_id}: {str(e)}"
                )]

        elif name == "get_themes_summary":
            try:
                summary = client.get_themes_summary()
                return [TextContent(
                    type="text",
                    text=json.dumps(summary, indent=2)
                )]
            except Exception as e:
                logger.error(f"get_themes_summary failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching themes summary: {str(e)}"
                )]

        # PRD-039: Symbol-Level Confluence Tools
        # PRD-049: Added try/catch and validation
        elif name == "get_symbol_analysis":
            symbol = arguments.get("symbol", "").upper()
            if not symbol:
                return [TextContent(
                    type="text",
                    text="Error: symbol is required"
                )]
            try:
                analysis = client.get_symbol_detail(symbol)
                return [TextContent(
                    type="text",
                    text=json.dumps(analysis, indent=2)
                )]
            except Exception as e:
                logger.error(f"get_symbol_analysis failed for {symbol}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching analysis for {symbol}: {str(e)}"
                )]

        elif name == "get_symbol_levels":
            symbol = arguments.get("symbol", "").upper()
            if not symbol:
                return [TextContent(
                    type="text",
                    text="Error: symbol is required"
                )]
            try:
                source = arguments.get("source")
                levels = client.get_symbol_levels(symbol, source)
                return [TextContent(
                    type="text",
                    text=json.dumps(levels, indent=2)
                )]
            except Exception as e:
                logger.error(f"get_symbol_levels failed for {symbol}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching levels for {symbol}: {str(e)}"
                )]

        elif name == "get_confluence_opportunities":
            try:
                opportunities = client.get_confluence_opportunities()
                return [TextContent(
                    type="text",
                    text=json.dumps(opportunities, indent=2)
                )]
            except Exception as e:
                logger.error(f"get_confluence_opportunities failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching confluence opportunities: {str(e)}"
                )]

        elif name == "get_trade_setup":
            symbol = arguments.get("symbol", "").upper()
            if not symbol:
                return [TextContent(
                    type="text",
                    text="Error: symbol is required"
                )]
            try:
                detail = client.get_symbol_detail(symbol)

                # Extract trade setup from confluence data
                trade_setup = {
                    "symbol": symbol,
                    "kt_bias": detail.get("kt_technical", {}).get("bias"),
                    "discord_quadrant": detail.get("discord_options", {}).get("quadrant"),
                    "confluence_score": detail.get("confluence", {}).get("score"),
                    "trade_setup": detail.get("confluence", {}).get("trade_setup"),
                    "levels": detail.get("levels", [])
                }

                return [TextContent(
                    type="text",
                    text=json.dumps(trade_setup, indent=2)
                )]
            except Exception as e:
                logger.error(f"get_trade_setup failed for {symbol}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error getting trade setup for {symbol}: {str(e)}"
                )]

        # PRD-044: Synthesis Quality Tool
        # PRD-049: Added try/catch and type validation
        elif name == "get_synthesis_quality":
            synthesis_id = arguments.get("synthesis_id")
            try:
                # Convert synthesis_id to int if provided
                if synthesis_id is not None:
                    synthesis_id = int(synthesis_id)
                quality = client.get_synthesis_quality(synthesis_id)
                return [TextContent(
                    type="text",
                    text=json.dumps(quality, indent=2)
                )]
            except ValueError:
                return [TextContent(
                    type="text",
                    text=f"Error: synthesis_id must be an integer, got '{arguments.get('synthesis_id')}'"
                )]
            except Exception as e:
                logger.error(f"get_synthesis_quality failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching synthesis quality: {str(e)}"
                )]

        # PRD-051: Individual Content Access Tools
        elif name == "list_recent_content":
            try:
                source = arguments.get("source")
                content_type = arguments.get("content_type")
                days = arguments.get("days", 7)
                limit = arguments.get("limit", 20)

                result = client.list_recent_content(
                    source=source,
                    content_type=content_type,
                    days=days,
                    limit=limit
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except Exception as e:
                logger.error(f"list_recent_content failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error listing recent content: {str(e)}"
                )]

        # New tools: synthesis history, quality, health, theme evolution
        elif name == "get_synthesis_history":
            try:
                limit = arguments.get("limit", 10)
                offset = arguments.get("offset", 0)
                limit = int(limit)
                offset = int(offset)
                result = client.get_synthesis_history(limit=limit, offset=offset)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except ValueError:
                return [TextContent(
                    type="text",
                    text="Error: limit and offset must be integers"
                )]
            except Exception as e:
                logger.error(f"get_synthesis_history failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching synthesis history: {str(e)}"
                )]

        elif name == "get_synthesis_by_id":
            synthesis_id = arguments.get("synthesis_id")
            if synthesis_id is None:
                return [TextContent(
                    type="text",
                    text="Error: synthesis_id is required"
                )]
            try:
                synthesis_id = int(synthesis_id)
                result = client.get_synthesis_by_id(synthesis_id)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except ValueError:
                return [TextContent(
                    type="text",
                    text=f"Error: synthesis_id must be an integer, got '{arguments.get('synthesis_id')}'"
                )]
            except Exception as e:
                logger.error(f"get_synthesis_by_id failed for id {synthesis_id}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching synthesis {synthesis_id}: {str(e)}"
                )]

        elif name == "get_quality_trends":
            try:
                days = arguments.get("days", 30)
                days = int(days)
                result = client.get_quality_trends(days=days)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except ValueError:
                return [TextContent(
                    type="text",
                    text="Error: days must be an integer"
                )]
            except Exception as e:
                logger.error(f"get_quality_trends failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching quality trends: {str(e)}"
                )]

        elif name == "get_quality_flagged":
            try:
                limit = arguments.get("limit", 10)
                limit = int(limit)
                result = client.get_quality_flagged(limit=limit)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except ValueError:
                return [TextContent(
                    type="text",
                    text="Error: limit must be an integer"
                )]
            except Exception as e:
                logger.error(f"get_quality_flagged failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching flagged syntheses: {str(e)}"
                )]

        elif name == "get_system_health":
            try:
                result = client.get_source_health()
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except Exception as e:
                logger.error(f"get_system_health failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching system health: {str(e)}"
                )]

        elif name == "get_active_alerts":
            try:
                include_acknowledged = arguments.get("include_acknowledged", False)
                result = client.get_active_alerts(include_acknowledged=bool(include_acknowledged))
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except Exception as e:
                logger.error(f"get_active_alerts failed: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching active alerts: {str(e)}"
                )]

        elif name == "get_theme_evolution":
            theme_id = arguments.get("theme_id")
            if theme_id is None:
                return [TextContent(
                    type="text",
                    text="Error: theme_id is required"
                )]
            try:
                theme_id = int(theme_id)
                result = client.get_theme_evolution(theme_id)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except ValueError:
                return [TextContent(
                    type="text",
                    text=f"Error: theme_id must be an integer, got '{arguments.get('theme_id')}'"
                )]
            except Exception as e:
                logger.error(f"get_theme_evolution failed for id {theme_id}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error fetching theme evolution {theme_id}: {str(e)}"
                )]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[MCP] Tool '{name}' failed after {elapsed:.2f}s: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
    finally:
        elapsed = time.time() - start_time
        logger.info(f"[MCP] Tool '{name}' completed in {elapsed:.2f}s")


async def run_stdio():
    """Run the MCP server in stdio mode."""
    from mcp.server.stdio import stdio_server
    logger.info("Starting Confluence Research MCP Server (stdio mode)...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def run_sse():
    """Run the MCP server in SSE (HTTP) mode."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    import uvicorn

    # Create SSE transport
    sse = SseServerTransport("/messages")

    async def handle_sse(request):
        """Handle SSE connections."""
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    async def handle_messages(request):
        """Handle message POST requests."""
        await sse.handle_post_message(request.scope, request.receive, request._send)

    async def health(request):
        """Health check endpoint."""
        return JSONResponse({"status": "ok", "server": "confluence-research"})

    # Create Starlette app
    app = Starlette(
        debug=True,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
            Route("/health", endpoint=health),
        ],
    )

    port = int(os.getenv("MCP_PORT", "8765"))
    logger.info(f"Starting Confluence Research MCP Server (SSE mode) on http://localhost:{port}/sse")
    print(f"\n{'='*60}")
    print(f"MCP Server running at: http://localhost:{port}/sse")
    print(f"Add this URL to Claude Desktop Settings > Integrations")
    print(f"{'='*60}\n")

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


async def main():
    """Run the MCP server."""
    if "--stdio" in sys.argv:
        await run_stdio()
    else:
        await run_sse()


if __name__ == "__main__":
    asyncio.run(main())
