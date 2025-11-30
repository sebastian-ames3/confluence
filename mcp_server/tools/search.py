"""
Search Content Tool

Searches collected research content by keyword.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from ..database import db
from ..config import MAX_SEARCH_RESULTS, DEFAULT_DAYS


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
    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    # Build query with optional source filter
    # Using LIKE for basic keyword matching (FTS can be added later)
    search_pattern = f"%{query}%"

    if source:
        sql = """
            SELECT
                rc.id,
                s.name as source,
                rc.content_type,
                rc.collected_at,
                COALESCE(json_extract(rc.json_metadata, '$.title'), s.name || ' content') as title,
                SUBSTR(rc.content_text, 1, 300) as snippet,
                ac.key_themes,
                ac.sentiment
            FROM raw_content rc
            JOIN sources s ON rc.source_id = s.id
            LEFT JOIN analyzed_content ac ON rc.id = ac.raw_content_id
            WHERE (rc.content_text LIKE ? OR json_extract(rc.json_metadata, '$.title') LIKE ?)
              AND s.name LIKE ?
              AND rc.collected_at >= ?
            ORDER BY rc.collected_at DESC
            LIMIT ?
        """
        params = (search_pattern, search_pattern, f"%{source}%", cutoff_str, limit)
    else:
        sql = """
            SELECT
                rc.id,
                s.name as source,
                rc.content_type,
                rc.collected_at,
                COALESCE(json_extract(rc.json_metadata, '$.title'), s.name || ' content') as title,
                SUBSTR(rc.content_text, 1, 300) as snippet,
                ac.key_themes,
                ac.sentiment
            FROM raw_content rc
            JOIN sources s ON rc.source_id = s.id
            LEFT JOIN analyzed_content ac ON rc.id = ac.raw_content_id
            WHERE (rc.content_text LIKE ? OR json_extract(rc.json_metadata, '$.title') LIKE ?)
              AND rc.collected_at >= ?
            ORDER BY rc.collected_at DESC
            LIMIT ?
        """
        params = (search_pattern, search_pattern, cutoff_str, limit)

    results = db.execute_query(sql, params)

    # Get total count
    if source:
        count_sql = """
            SELECT COUNT(*) as total
            FROM raw_content rc
            JOIN sources s ON rc.source_id = s.id
            WHERE (rc.content_text LIKE ? OR json_extract(rc.json_metadata, '$.title') LIKE ?)
              AND s.name LIKE ?
              AND rc.collected_at >= ?
        """
        count_params = (search_pattern, search_pattern, f"%{source}%", cutoff_str)
    else:
        count_sql = """
            SELECT COUNT(*) as total
            FROM raw_content rc
            WHERE (rc.content_text LIKE ? OR json_extract(rc.json_metadata, '$.title') LIKE ?)
              AND rc.collected_at >= ?
        """
        count_params = (search_pattern, search_pattern, cutoff_str)

    count_result = db.execute_one(count_sql, count_params)
    total_matches = count_result["total"] if count_result else 0

    # Format results
    formatted_results = []
    for row in results:
        formatted_results.append({
            "title": row["title"],
            "source": row["source"],
            "date": row["collected_at"][:10] if row["collected_at"] else None,
            "type": row["content_type"],
            "snippet": row["snippet"],
            "themes": row["key_themes"].split(",") if row["key_themes"] else [],
            "sentiment": row["sentiment"]
        })

    return {
        "results": formatted_results,
        "total_matches": total_matches,
        "query": query,
        "days_searched": days
    }
