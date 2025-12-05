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
    extract_source_stances,
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

Returns the full v3 synthesis including:
- Executive summary (what your sources are saying)
- Confluence zones (where sources align)
- Conflict watch (where sources disagree)
- Attention priorities (what to focus on)
- Re-review recommendations (older content now relevant)
- Source stances (what each source is thinking)
- Catalyst calendar (upcoming events)

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
- youtube (macro commentary)
- substack (thematic research)

Returns:
- Narrative of what the source is thinking
- Key themes they're focused on
- Overall bias (bullish, bearish, cautious, neutral, mixed)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source name: discord, 42macro, kt_technical, youtube, or substack"
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
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
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
            stances = extract_source_stances(synthesis)

            # Find matching source (case-insensitive)
            matched_stance = None
            for key, value in stances.items():
                if key.lower() == source or source in key.lower():
                    matched_stance = {"source": key, **value}
                    break

            if matched_stance:
                return [TextContent(
                    type="text",
                    text=json.dumps(matched_stance, indent=2)
                )]
            else:
                available = list(stances.keys())
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

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


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
