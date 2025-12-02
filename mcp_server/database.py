"""
Database Connection for MCP Server

DEPRECATED: Direct database access for MCP Server.

This module is deprecated as of PRD-016.
MCP tools now use API proxy pattern via api_client.py.

The MCP server now fetches data via HTTP API calls to the Railway deployment
instead of directly querying a local SQLite database. This fixes the
architecture gap where Claude Desktop (running locally) cannot access the
production database (on Railway).

This module is kept for backwards compatibility with local development only.
Use mcp_server.api_client for production deployments.
"""

import warnings
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

from .config import DATABASE_PATH

# Issue deprecation warning when this module is imported
warnings.warn(
    "mcp_server.database is deprecated as of PRD-016. "
    "Use mcp_server.api_client instead for production deployments. "
    "Direct database access is kept for local development only.",
    DeprecationWarning,
    stacklevel=2
)


class MCPDatabase:
    """
    Read-only database connection for MCP queries.

    DEPRECATED: Use api_client.APIClient instead for production.
    This class is kept for backwards compatibility with local development.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database (defaults to config value)
        """
        self.db_path = db_path or DATABASE_PATH

    @contextmanager
    def get_connection(self):
        """Get a read-only database connection."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        # Enable read-only mode for safety
        conn.execute("PRAGMA query_only = ON")
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a read-only query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of row dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def execute_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """
        Execute a query returning a single row.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Row dictionary or None
        """
        results = self.execute_query(query, params)
        return results[0] if results else None


# Global database instance (deprecated)
db = MCPDatabase()
