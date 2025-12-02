"""
Get Source View Tool

Gets a specific source's current view on a topic.

PRD-016: Refactored to use API proxy pattern instead of direct database access.
"""

from typing import Dict, Any
import logging

from ..api_client import api, APIError, handle_api_error

logger = logging.getLogger(__name__)


def get_source_view(
    source: str,
    topic: str
) -> Dict[str, Any]:
    """
    Get a specific source's current view on a topic.

    Args:
        source: Source name (e.g., "42macro", "discord")
        topic: Topic to query (e.g., "equities", "gold", "volatility")

    Returns:
        Dictionary with source's view on the topic
    """
    try:
        # Build query parameters
        params = {
            "topic": topic
        }

        # Call the source view API endpoint
        response = api.get(f"/api/search/sources/{source}/view", params=params)

        # Check for message (no content found or source not found)
        if response.get("current_view") is None and response.get("message"):
            return {
                "source": source,
                "topic": topic,
                "current_view": None,
                "message": response.get("message"),
                "related_content": []
            }

        # Return the source view data
        return {
            "source": response.get("source", source),
            "topic": topic,
            "current_view": response.get("current_view"),
            "avg_sentiment": response.get("avg_sentiment"),
            "avg_conviction": response.get("avg_conviction"),
            "last_mentioned": response.get("last_mentioned"),
            "context": response.get("context"),
            "mentions_count": response.get("mentions_count", 0),
            "related_content": response.get("related_content", [])
        }

    except APIError as e:
        logger.error(f"Source view API error: {e.message}")
        return {
            **handle_api_error(e),
            "source": source,
            "topic": topic,
            "current_view": None,
            "related_content": []
        }

    except Exception as e:
        logger.error(f"Unexpected error in get_source_view: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "source": source,
            "topic": topic,
            "current_view": None,
            "related_content": []
        }
