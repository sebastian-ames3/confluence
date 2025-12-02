"""
Get Synthesis Tool

Retrieves the latest AI-generated research synthesis.

PRD-016: Refactored to use API proxy pattern instead of direct database access.
"""

from typing import Dict, Any
import logging

from ..api_client import api, APIError, handle_api_error

logger = logging.getLogger(__name__)


def get_synthesis(time_window: str = "24h") -> Dict[str, Any]:
    """
    Retrieve the latest AI-generated synthesis.

    Args:
        time_window: Time window filter ("24h", "7d", "30d")

    Returns:
        Dictionary with synthesis content and metadata
    """
    valid_windows = ["24h", "7d", "30d"]
    if time_window not in valid_windows:
        return {
            "error": f"Invalid time_window. Use: {valid_windows}",
            "synthesis": None
        }

    try:
        # Build query parameters
        params = {}
        if time_window:
            params["time_window"] = time_window

        # Call the synthesis API endpoint
        response = api.get("/api/synthesis/latest", params=params)

        # Check if synthesis was found
        if response.get("status") == "not_found":
            return {
                "synthesis": None,
                "message": response.get("message", f"No synthesis found for time window: {time_window}")
            }

        # Return the synthesis data
        return {
            "id": response.get("id"),
            "synthesis": response.get("synthesis"),
            "key_themes": response.get("key_themes", []),
            "high_conviction_ideas": response.get("high_conviction_ideas", []),
            "contradictions": response.get("contradictions", []),
            "market_regime": response.get("market_regime"),
            "catalysts": response.get("catalysts", []),
            "time_window": response.get("time_window"),
            "content_count": response.get("content_count"),
            "sources_included": response.get("sources_included", []),
            "focus_topic": response.get("focus_topic"),
            "generated_at": response.get("generated_at")
        }

    except APIError as e:
        logger.error(f"Synthesis API error: {e.message}")
        return {
            **handle_api_error(e),
            "synthesis": None
        }

    except Exception as e:
        logger.error(f"Unexpected error in get_synthesis: {e}")
        return {
            "error": f"Unexpected error: {str(e)}",
            "synthesis": None
        }
