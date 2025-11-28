#!/usr/bin/env python3
"""
Macro Confluence Hub - MCP Server

Model Context Protocol server for Claude Desktop integration.
Exposes tools for querying research data via natural language.

This implementation uses JSON-RPC over stdio, compatible with MCP spec.
Works with Python 3.9+ (no mcp package required).

Usage:
    python -m mcp_server.server

Configuration:
    Set DATABASE_PATH environment variable to point to your database.
    Default: database/confluence.db
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional

from .config import SERVER_NAME, SERVER_VERSION
from .tools import (
    search_content,
    get_synthesis,
    get_themes,
    get_recent,
    get_source_view
)

# Configure logging to stderr (stdout is for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


# Tool definitions for MCP
TOOLS = [
    {
        "name": "search_content",
        "description": "Search collected research content by keyword. Use this to find what sources have said about specific topics like 'gold', 'equities', 'volatility', etc.",
        "inputSchema": {
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
    },
    {
        "name": "get_synthesis",
        "description": "Get the latest AI-generated research synthesis. This provides a summary of key themes, high conviction ideas, and market regime from recent research.",
        "inputSchema": {
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
    },
    {
        "name": "get_themes",
        "description": "List currently tracked macro themes from collected research. Shows which themes are mentioned across multiple sources.",
        "inputSchema": {
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
    },
    {
        "name": "get_recent",
        "description": "Get recent content from a specific source. Use this to see what a particular source (like '42macro' or 'discord') has published recently.",
        "inputSchema": {
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
    },
    {
        "name": "get_source_view",
        "description": "Get a specific source's current view on a topic. Use this to understand what a particular analyst or source thinks about something.",
        "inputSchema": {
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
    }
]


def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle initialize request."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION
        }
    }


def handle_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/list request."""
    return {"tools": TOOLS}


def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call request."""
    name = params.get("name")
    arguments = params.get("arguments", {})

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
            return {
                "content": [{"type": "text", "text": json.dumps({"error": f"Unknown tool: {name}"})}],
                "isError": True
            }

        return {
            "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}]
        }

    except Exception as e:
        logger.error(f"Tool {name} failed: {str(e)}")
        return {
            "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
            "isError": True
        }


def process_request(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process a JSON-RPC request and return response."""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    logger.info(f"Processing request: {method}")

    # Handle notifications (no response needed)
    if request_id is None:
        if method == "notifications/initialized":
            logger.info("Client initialized")
        return None

    # Handle requests
    if method == "initialize":
        result = handle_initialize(params)
    elif method == "tools/list":
        result = handle_tools_list(params)
    elif method == "tools/call":
        result = handle_tools_call(params)
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }


async def run_server():
    """Run the MCP server using stdio."""
    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION}")

    # Read from stdin, write to stdout
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)

    loop = asyncio.get_event_loop()
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    writer_transport, writer_protocol = await loop.connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, loop)

    while True:
        try:
            # Read line from stdin
            line = await reader.readline()
            if not line:
                break

            line = line.decode('utf-8').strip()
            if not line:
                continue

            # Parse JSON-RPC request
            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                continue

            # Process request
            response = process_request(request)

            # Send response if needed
            if response is not None:
                response_line = json.dumps(response) + "\n"
                writer.write(response_line.encode('utf-8'))
                await writer.drain()

        except Exception as e:
            logger.error(f"Server error: {e}")
            break

    logger.info("Server shutting down")


def main():
    """Entry point."""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")


if __name__ == "__main__":
    main()
