"""
Search Content Tool

Searches collected research content by keyword.

PRD-016: Refactored to use API proxy pattern instead of direct database access.
"""

from typing import Optional, Dict, Any
import logging

from ..api_client import api, APIError, handle_api_error
from ..config import MAX_SEARCH_RESULTS, DEFAULT_DAYS

logger = logging.getLogger(__name__)


def search_content(
    query: str,
    source: Optional[str] = None,
    days: int = DEFAULT_DAYS,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Search collected research content by keyword.

    Args:
        query: Search query (keywords)
        source: Optional source filter (e.g., "42macro", "discord")
        days: Number of days to search (default 7)
        limit: Maximum results to return (default 10)

    Returns:
        Dictionary with search results and total count
    """
    limit = min(limit, MAX_SEARCH_RESULTS)

    try:
        # Build query parameters
        params = {
            "q": query,
            "days": days,
            "limit": limit
        }
        if source:
            params["source"] = source

        # Call the search API endpoint
        response = api.get("/api/search/content", params=params)

        # The API response already matches our expected format
        return {
            "results": response.get("results", []),
            "total_matches": response.get("total_matches", 0),
            "query": query,
            "days_searched": days
        }

    except APIError as e:
        logger.error(f"Search API error: {e.message}")
        return {
            **handle_api_error(e),
            "results": [],
            "total_matches": 0,
            "query": query,
            "days_searched": days
        }

    except Exception as e:
        logger.error(f"Unexpected error in search_content: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "results": [],
            "total_matches": 0,
            "query": query,
            "days_searched": days
        }
