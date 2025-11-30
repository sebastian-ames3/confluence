"""
Get Themes Tool

Lists currently tracked macro themes from collected research.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from ..database import db


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
    # Define "active" as last 7 days
    if active_only:
        cutoff = datetime.utcnow() - timedelta(days=7)
        cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")
    else:
        cutoff_str = "1970-01-01 00:00:00"

    # Get themes from analyzed content
    sql = """
        SELECT
            ac.key_themes,
            s.name as source,
            ac.analyzed_at,
            ac.sentiment,
            ac.conviction
        FROM analyzed_content ac
        JOIN raw_content rc ON ac.raw_content_id = rc.id
        JOIN sources s ON rc.source_id = s.id
        WHERE ac.analyzed_at >= ?
          AND ac.key_themes IS NOT NULL
          AND ac.key_themes != ''
        ORDER BY ac.analyzed_at DESC
    """

    results = db.execute_query(sql, (cutoff_str,))

    # Aggregate themes across sources
    theme_data: Dict[str, Dict] = {}

    for row in results:
        themes = row["key_themes"].split(",") if row["key_themes"] else []
        source = row["source"]
        analyzed_at = row["analyzed_at"]
        sentiment = row["sentiment"]
        conviction = row["conviction"]

        for theme in themes:
            theme = theme.strip()
            if not theme:
                continue

            if theme not in theme_data:
                theme_data[theme] = {
                    "name": theme,
                    "sources": set(),
                    "first_seen": analyzed_at,
                    "last_seen": analyzed_at,
                    "mention_count": 0,
                    "sentiments": [],
                    "convictions": []
                }

            theme_data[theme]["sources"].add(source)
            theme_data[theme]["mention_count"] += 1
            if analyzed_at < theme_data[theme]["first_seen"]:
                theme_data[theme]["first_seen"] = analyzed_at
            if analyzed_at > theme_data[theme]["last_seen"]:
                theme_data[theme]["last_seen"] = analyzed_at
            # Convert sentiment/conviction to float if they're numeric
            if sentiment is not None:
                try:
                    theme_data[theme]["sentiments"].append(float(sentiment))
                except (ValueError, TypeError):
                    pass  # Skip non-numeric sentiments
            if conviction is not None:
                try:
                    theme_data[theme]["convictions"].append(float(conviction))
                except (ValueError, TypeError):
                    pass  # Skip non-numeric convictions

    # Filter by min_sources and format output
    themes_list: List[Dict] = []
    for theme, data in theme_data.items():
        if len(data["sources"]) >= min_sources:
            # Calculate average sentiment and conviction
            avg_sentiment = None
            if data["sentiments"]:
                avg_sentiment = sum(data["sentiments"]) / len(data["sentiments"])

            avg_conviction = None
            if data["convictions"]:
                avg_conviction = sum(data["convictions"]) / len(data["convictions"])

            # Determine conviction trend
            conviction_trend = "stable"
            if len(data["convictions"]) >= 3:
                recent = data["convictions"][-3:]
                if all(recent[i] <= recent[i+1] for i in range(len(recent)-1)):
                    conviction_trend = "rising"
                elif all(recent[i] >= recent[i+1] for i in range(len(recent)-1)):
                    conviction_trend = "falling"

            themes_list.append({
                "name": data["name"],
                "sources": list(data["sources"]),
                "source_count": len(data["sources"]),
                "mention_count": data["mention_count"],
                "first_seen": data["first_seen"][:10] if data["first_seen"] else None,
                "last_seen": data["last_seen"][:10] if data["last_seen"] else None,
                "avg_sentiment": round(avg_sentiment, 2) if avg_sentiment else None,
                "avg_conviction": round(avg_conviction, 2) if avg_conviction else None,
                "conviction_trend": conviction_trend
            })

    # Sort by mention count (most mentioned first)
    themes_list.sort(key=lambda x: x["mention_count"], reverse=True)

    return {
        "themes": themes_list,
        "total_themes": len(themes_list),
        "active_only": active_only,
        "min_sources": min_sources
    }
