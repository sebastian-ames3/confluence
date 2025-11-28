"""
MCP Server Configuration

Loads configuration from environment variables or defaults.
"""

import os
from pathlib import Path

# Database path - can be overridden via environment variable
DEFAULT_DB_PATH = Path(__file__).parent.parent / "database" / "confluence.db"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))

# Server settings
SERVER_NAME = "confluence-hub"
SERVER_VERSION = "1.0.0"

# Query limits to prevent timeouts
MAX_SEARCH_RESULTS = 50
MAX_RECENT_ITEMS = 100
DEFAULT_DAYS = 7
