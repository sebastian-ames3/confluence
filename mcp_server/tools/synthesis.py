"""
Get Synthesis Tool

Retrieves the latest AI-generated research synthesis.
"""

import json
from typing import Optional, Dict, Any

from ..database import db


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

    sql = """
        SELECT
            id,
            synthesis,
            key_themes,
            high_conviction_ideas,
            contradictions,
            market_regime,
            catalysts,
            time_window,
            content_count,
            sources_included,
            focus_topic,
            generated_at
        FROM syntheses
        WHERE time_window = ?
        ORDER BY generated_at DESC
        LIMIT 1
    """

    result = db.execute_one(sql, (time_window,))

    if not result:
        return {
            "synthesis": None,
            "message": f"No synthesis found for time window: {time_window}"
        }

    # Parse JSON fields
    def parse_json_field(value):
        if not value:
            return []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []

    return {
        "id": result["id"],
        "synthesis": result["synthesis"],
        "key_themes": parse_json_field(result["key_themes"]),
        "high_conviction_ideas": parse_json_field(result["high_conviction_ideas"]),
        "contradictions": parse_json_field(result["contradictions"]),
        "market_regime": result["market_regime"],
        "catalysts": parse_json_field(result["catalysts"]),
        "time_window": result["time_window"],
        "content_count": result["content_count"],
        "sources_included": parse_json_field(result["sources_included"]),
        "focus_topic": result["focus_topic"],
        "generated_at": result["generated_at"]
    }
