"""
Get Recent Tool

Gets recent collections from specific sources.

PRD-016: Refactored to use API proxy pattern instead of direct database access.
"""

from typing import Optional, Dict, Any
import logging

from ..api_client import api, APIError, handle_api_error
from ..config import MAX_RECENT_ITEMS

logger = logging.getLogger(__name__)


def get_recent(
    source: str,
    days: int = 3,
    content_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get recent collections from a specific source.

    Args:
        source: Source name (e.g., "discord", "42macro")
        days: Number of days to look back (default 3)
        content_type: Optional filter by content type ("video", "pdf", "text", "image")

    Returns:
        Dictionary with recent items from the source
    """
    try:
        # Build query parameters
        params = {
            "days": days,
            "limit": MAX_RECENT_ITEMS
        }
        if content_type:
            params["content_type"] = content_type

        # Call the recent content API endpoint
        response = api.get(f"/api/search/recent/{source}", params=params)

        # Check for error message (source not found)
        if response.get("message"):
            return {
                "source": source,
                "items": [],
                "count": 0,
                "days": days,
                "content_type_filter": content_type,
                "message": response.get("message")
            }

        # Return the recent items
        return {
            "source": response.get("source", source),
            "items": response.get("items", []),
            "count": response.get("count", 0),
            "days": days,
            "content_type_filter": content_type
        }

    except APIError as e:
        logger.error(f"Recent API error: {e.message}")
        return {
            **handle_api_error(e),
            "source": source,
            "items": [],
            "count": 0,
            "days": days,
            "content_type_filter": content_type
        }

    except Exception as e:
        logger.error(f"Unexpected error in get_recent: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "source": source,
            "items": [],
            "count": 0,
            "days": days,
            "content_type_filter": content_type
        }
