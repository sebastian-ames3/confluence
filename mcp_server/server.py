#!/usr/bin/env python3
"""
Macro Confluence Hub - MCP Server

Model Context Protocol server for Claude Desktop integration.
Exposes tools for querying research data via natural language.

Uses the official MCP SDK (requires Python 3.10+).

Usage:
    python -m mcp_server.server

Configuration:
    Set DATABASE_PATH environment variable to point to your database.
    Default: database/confluence.db
"""

import json
import logging
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .config import SERVER_NAME, SERVER_VERSION
from .tools import (
    search_content,
    get_synthesis,
    get_themes,
    get_recent,
    get_source_view
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create MCP server instance
server = Server(SERVER_NAME)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools for Claude."""
    return [
        Tool(
            name="search_content",
            description="Search collected research content by keyword. Use this to find what sources have said about specific topics like 'gold', 'equities', 'volatility', etc.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keywords (e.g., 'gold positioning', 'Fed policy')"
                    },
                    "source": {
                        "type": "string",
                        "description": "Optional: Filter by source (e.g., '42macro', 'discord', 'youtube')"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to search back (default: 7)",
                        "default": 7
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_synthesis",
            description="Get the latest AI-generated research synthesis. This provides a summary of key themes, high conviction ideas, and market regime from recent research.",
            inputSchema={
                "type": "object",
                "properties": {
                    "time_window": {
                        "type": "string",
                        "description": "Time window for synthesis: '24h', '7d', or '30d'",
                        "enum": ["24h", "7d", "30d"],
                        "default": "24h"
                    }
                }
            }
        ),
        Tool(
            name="get_themes",
            description="List currently tracked macro themes from collected research. Shows which themes are mentioned across multiple sources.",
            inputSchema={
                "type": "object",
                "properties": {
                    "active_only": {
                        "type": "boolean",
                        "description": "Only include themes from the last 7 days (default: true)",
                        "default": True
                    },
                    "min_sources": {
                        "type": "integer",
                        "description": "Minimum number of sources mentioning the theme (default: 1)",
                        "default": 1
                    }
                }
            }
        ),
        Tool(
            name="get_recent",
            description="Get recent content from a specific source. Use this to see what a particular source (like '42macro' or 'discord') has published recently.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source name (e.g., 'discord', '42macro', 'youtube', 'substack')"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 3)",
                        "default": 3
                    },
                    "content_type": {
                        "type": "string",
                        "description": "Optional: Filter by content type ('video', 'pdf', 'text', 'image')"
                    }
                },
                "required": ["source"]
            }
        ),
        Tool(
            name="get_source_view",
            description="Get a specific source's current view on a topic. Use this to understand what a particular analyst or source thinks about something.",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source name (e.g., '42macro', 'discord')"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Topic to query (e.g., 'equities', 'gold', 'volatility', 'Fed')"
                    }
                },
                "required": ["source", "topic"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool invocations from Claude."""
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    try:
        if name == "search_content":
            result = search_content(
                query=arguments["query"],
                source=arguments.get("source"),
                days=arguments.get("days", 7),
                limit=arguments.get("limit", 10)
            )
        elif name == "get_synthesis":
            result = get_synthesis(
                time_window=arguments.get("time_window", "24h")
            )
        elif name == "get_themes":
            result = get_themes(
                active_only=arguments.get("active_only", True),
                min_sources=arguments.get("min_sources", 1)
            )
        elif name == "get_recent":
            result = get_recent(
                source=arguments["source"],
                days=arguments.get("days", 3),
                content_type=arguments.get("content_type")
            )
        elif name == "get_source_view":
            result = get_source_view(
                source=arguments["source"],
                topic=arguments["topic"]
            )
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]

    except Exception as e:
        logger.error(f"Tool {name} failed: {str(e)}")
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)})
        )]


async def main():
    """Run the MCP server."""
    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION}")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
