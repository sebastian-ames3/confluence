"""
Get Source View Tool

Gets a specific source's current view on a topic.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from ..database import db


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
    # Search for content from this source mentioning the topic
    search_pattern = f"%{topic}%"
    cutoff = datetime.utcnow() - timedelta(days=14)
    cutoff_str = cutoff.strftime("%Y-%m-%d %H:%M:%S")

    sql = """
        SELECT
            rc.id,
            rc.content_type,
            rc.collected_at,
            rc.json_metadata,
            SUBSTR(rc.content_text, 1, 1000) as content_excerpt,
            ac.key_themes,
            ac.sentiment,
            ac.conviction,
            ac.tickers_mentioned,
            ac.analysis_result
        FROM raw_content rc
        JOIN sources s ON rc.source_id = s.id
        LEFT JOIN analyzed_content ac ON rc.id = ac.raw_content_id
        WHERE s.name LIKE ?
          AND rc.collected_at >= ?
          AND (
              rc.content_text LIKE ?
              OR ac.key_themes LIKE ?
              OR json_extract(rc.json_metadata, '$.title') LIKE ?
          )
        ORDER BY rc.collected_at DESC
        LIMIT 10
    """

    params = (
        f"%{source}%",
        cutoff_str,
        search_pattern,
        search_pattern,
        search_pattern
    )

    results = db.execute_query(sql, params)

    if not results:
        return {
            "source": source,
            "topic": topic,
            "current_view": None,
            "message": f"No content found from {source} about {topic} in the last 14 days",
            "related_content": []
        }

    # Analyze the results to determine current view
    sentiments = []
    convictions = []
    related_content: List[Dict] = []
    last_mentioned = None
    context_snippets = []

    for row in results:
        # Parse metadata
        metadata = {}
        if row["json_metadata"]:
            try:
                metadata = json.loads(row["json_metadata"])
            except json.JSONDecodeError:
                pass

        # Track sentiment and conviction
        if row["sentiment"] is not None:
            sentiments.append(row["sentiment"])
        if row["conviction"] is not None:
            convictions.append(row["conviction"])

        # Track last mentioned
        if row["collected_at"]:
            if last_mentioned is None or row["collected_at"] > last_mentioned:
                last_mentioned = row["collected_at"]

        # Extract context
        if row["content_excerpt"]:
            # Find sentences containing the topic
            sentences = row["content_excerpt"].replace("\n", " ").split(".")
            for sentence in sentences:
                if topic.lower() in sentence.lower():
                    context_snippets.append(sentence.strip() + ".")
                    break

        # Parse analysis for summary
        summary = None
        if row["analysis_result"]:
            try:
                analysis = json.loads(row["analysis_result"])
                summary = analysis.get("summary")
            except json.JSONDecodeError:
                pass

        related_content.append({
            "title": metadata.get("title", f"{source} content"),
            "date": row["collected_at"][:10] if row["collected_at"] else None,
            "type": row["content_type"],
            "themes": row["key_themes"].split(",") if row["key_themes"] else [],
            "summary": summary,
            "tickers": row["tickers_mentioned"].split(",") if row["tickers_mentioned"] else []
        })

    # Determine current view based on average sentiment
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else None
    avg_conviction = sum(convictions) / len(convictions) if convictions else None

    if avg_sentiment is not None:
        if avg_sentiment >= 0.6:
            current_view = "bullish"
        elif avg_sentiment >= 0.4:
            current_view = "cautiously bullish"
        elif avg_sentiment >= 0.3:
            current_view = "neutral"
        elif avg_sentiment >= 0.2:
            current_view = "cautiously bearish"
        else:
            current_view = "bearish"
    else:
        current_view = "unclear"

    # Build context from snippets
    context = " ".join(context_snippets[:3]) if context_snippets else None

    return {
        "source": source,
        "topic": topic,
        "current_view": current_view,
        "avg_sentiment": round(avg_sentiment, 2) if avg_sentiment else None,
        "avg_conviction": round(avg_conviction, 2) if avg_conviction else None,
        "last_mentioned": last_mentioned[:10] if last_mentioned else None,
        "context": context,
        "mentions_count": len(results),
        "related_content": related_content[:5]  # Top 5 related items
    }
