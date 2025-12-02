"""
MCP Server Configuration

Loads configuration from environment variables or defaults.

PRD-016: Added API configuration for Railway API proxy pattern.
The MCP server now fetches data via HTTP API instead of direct database access,
enabling Claude Desktop to access production data from anywhere.
"""

import os
from pathlib import Path

# =============================================================================
# API Configuration (PRD-016)
# =============================================================================
# The MCP server connects to the Railway API to fetch data.
# This allows Claude Desktop running locally to access production data.

API_BASE_URL = os.getenv("RAILWAY_API_URL", "http://localhost:8000")
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")

# Request settings
REQUEST_TIMEOUT = float(os.getenv("MCP_REQUEST_TIMEOUT", "30.0"))  # seconds

# =============================================================================
# Legacy Database Configuration (Deprecated)
# =============================================================================
# Direct database access is deprecated as of PRD-016.
# Kept for backwards compatibility with local development.

DEFAULT_DB_PATH = Path(__file__).parent.parent / "database" / "confluence.db"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))

# =============================================================================
# Server Settings
# =============================================================================

SERVER_NAME = "confluence-hub"
SERVER_VERSION = "1.1.0"  # Bumped for API proxy refactor (PRD-016)

# =============================================================================
# Query Limits
# =============================================================================

MAX_SEARCH_RESULTS = 50
MAX_RECENT_ITEMS = 100
DEFAULT_DAYS = 7
