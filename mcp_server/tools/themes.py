"""
Get Themes Tool

Lists currently tracked macro themes from collected research.

PRD-016: Refactored to use API proxy pattern instead of direct database access.
"""

from typing import Dict, Any
import logging

from ..api_client import api, APIError, handle_api_error

logger = logging.getLogger(__name__)


def get_themes(
    active_only: bool = True,
    min_sources: int = 1
) -> Dict[str, Any]:
    """
    List currently tracked macro themes.

    Args:
        active_only: Only include themes from recent content (default True)
        min_sources: Minimum number of sources mentioning theme (default 1)

    Returns:
        Dictionary with themes and their metadata
    """
    try:
        # Build query parameters
        params = {
            "active_only": active_only,
            "min_sources": min_sources
        }

        # Call the aggregated themes API endpoint
        # This endpoint aggregates themes from analyzed content
        response = api.get("/api/search/themes/aggregated", params=params)

        # Return the themes data
        return {
            "themes": response.get("themes", []),
            "total_themes": response.get("total_themes", 0),
            "active_only": active_only,
            "min_sources": min_sources
        }

    except APIError as e:
        logger.error(f"Themes API error: {e.message}")
        return {
            **handle_api_error(e),
            "themes": [],
            "total_themes": 0,
            "active_only": active_only,
            "min_sources": min_sources
        }

    except Exception as e:
        logger.error(f"Unexpected error in get_themes: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "themes": [],
            "total_themes": 0,
            "active_only": active_only,
            "min_sources": min_sources
        }
