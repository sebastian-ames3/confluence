"""
Get Recent Tool

Gets recent collections from specific sources.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

from ..database import db
from ..config import MAX_RECENT_ITEMS


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
    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    # Build query with optional content type filter
    if content_type:
        sql = """
            SELECT
                rc.id,
                rc.content_type,
                rc.collected_at,
                rc.json_metadata,
                SUBSTR(rc.content_text, 1, 500) as content_preview,
                ac.key_themes,
                ac.sentiment,
                ac.conviction,
                ac.analysis_result
            FROM raw_content rc
            JOIN sources s ON rc.source_id = s.id
            LEFT JOIN analyzed_content ac ON rc.id = ac.raw_content_id
            WHERE s.name LIKE ?
              AND rc.collected_at >= ?
              AND rc.content_type = ?
            ORDER BY rc.collected_at DESC
            LIMIT ?
        """
        params = (f"%{source}%", cutoff_str, content_type, MAX_RECENT_ITEMS)
    else:
        sql = """
            SELECT
                rc.id,
                rc.content_type,
                rc.collected_at,
                rc.json_metadata,
                SUBSTR(rc.content_text, 1, 500) as content_preview,
                ac.key_themes,
                ac.sentiment,
                ac.conviction,
                ac.analysis_result
            FROM raw_content rc
            JOIN sources s ON rc.source_id = s.id
            LEFT JOIN analyzed_content ac ON rc.id = ac.raw_content_id
            WHERE s.name LIKE ?
              AND rc.collected_at >= ?
            ORDER BY rc.collected_at DESC
            LIMIT ?
        """
        params = (f"%{source}%", cutoff_str, MAX_RECENT_ITEMS)

    results = db.execute_query(sql, params)

    # Format results
    items: List[Dict] = []
    for row in results:
        # Parse metadata
        metadata = {}
        if row["json_metadata"]:
            try:
                metadata = json.loads(row["json_metadata"])
            except json.JSONDecodeError:
                pass

        # Parse analysis result for summary
        summary = None
        if row["analysis_result"]:
            try:
                analysis = json.loads(row["analysis_result"])
                summary = analysis.get("summary", row["content_preview"][:200] if row["content_preview"] else None)
            except json.JSONDecodeError:
                summary = row["content_preview"][:200] if row["content_preview"] else None
        else:
            summary = row["content_preview"][:200] if row["content_preview"] else None

        items.append({
            "id": row["id"],
            "title": metadata.get("title", f"{source} content"),
            "type": row["content_type"],
            "date": row["collected_at"][:10] if row["collected_at"] else None,
            "datetime": row["collected_at"],
            "summary": summary,
            "themes": row["key_themes"].split(",") if row["key_themes"] else [],
            "sentiment": row["sentiment"],
            "conviction": row["conviction"],
            "url": metadata.get("url") or metadata.get("video_url")
        })

    return {
        "source": source,
        "items": items,
        "count": len(items),
        "days": days,
        "content_type_filter": content_type
    }
