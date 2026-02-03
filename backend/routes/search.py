"""
Search Routes

API endpoints for searching collected research content.
Part of PRD-016: MCP Server API Proxy Refactor.

These endpoints support the MCP server's search functionality,
allowing Claude Desktop to search content via API calls.

Security (PRD-015):
- All endpoints require HTTP Basic Auth
- Rate limited to prevent abuse

PRD-035: Migrated to async ORM using SQLAlchemy AsyncSession.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta
import json

from backend.models import (
    get_async_db,
    RawContent,
    AnalyzedContent,
    Source
)
from backend.utils.auth import verify_jwt_or_basic
from backend.utils.rate_limiter import limiter, RATE_LIMITS
from backend.utils.sanitization import sanitize_search_query

router = APIRouter()


@router.get("/content")
@limiter.limit(RATE_LIMITS["search"])
async def search_content(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    source: Optional[str] = Query(None, description="Filter by source name"),
    days: int = Query(7, ge=1, le=365, description="Number of days to search"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: AsyncSession = Depends(get_async_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Search collected research content by keyword.

    Searches content text, titles, and themes for matching keywords.
    Supports filtering by source and time window.

    Args:
        q: Search query (keywords)
        source: Optional source filter (e.g., "42macro", "discord")
        days: Number of days to search (default 7)
        limit: Maximum results to return (default 10)

    Returns:
        Dictionary with search results and metadata
    """
    # PRD-037/046: Sanitize search query and source filter
    q = sanitize_search_query(q)
    safe_source = sanitize_search_query(source) if source else None

    # Calculate cutoff date
    cutoff = datetime.utcnow() - timedelta(days=days)
    search_pattern = f"%{q}%"

    # Build query with joins
    stmt = (
        select(RawContent, AnalyzedContent, Source)
        .outerjoin(AnalyzedContent, RawContent.id == AnalyzedContent.raw_content_id)
        .join(Source, RawContent.source_id == Source.id)
        .where(RawContent.collected_at >= cutoff)
    )

    # Apply source filter if provided (PRD-046: sanitized)
    if safe_source:
        stmt = stmt.where(Source.name.ilike(f"%{safe_source}%"))

    # Apply search filter - search in content text and metadata
    stmt = stmt.where(
        (RawContent.content_text.ilike(search_pattern)) |
        (RawContent.json_metadata.ilike(search_pattern)) |
        (AnalyzedContent.key_themes.ilike(search_pattern))
    )

    # Order by recency
    stmt = stmt.order_by(desc(RawContent.collected_at))

    # Get total count (separate query for efficiency)
    count_stmt = (
        select(func.count())
        .select_from(RawContent)
        .outerjoin(AnalyzedContent, RawContent.id == AnalyzedContent.raw_content_id)
        .join(Source, RawContent.source_id == Source.id)
        .where(RawContent.collected_at >= cutoff)
        .where(
            (RawContent.content_text.ilike(search_pattern)) |
            (RawContent.json_metadata.ilike(search_pattern)) |
            (AnalyzedContent.key_themes.ilike(search_pattern))
        )
    )
    if safe_source:
        count_stmt = count_stmt.where(Source.name.ilike(f"%{safe_source}%"))

    count_result = await db.execute(count_stmt)
    total_matches = count_result.scalar() or 0

    # Apply limit
    stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    results = result.all()

    # Format results
    formatted_results = []
    for raw, analyzed, src in results:
        # Parse metadata for title and url
        title = f"{src.name} content"
        metadata = {}
        if raw.json_metadata:
            try:
                metadata = json.loads(raw.json_metadata)
                title = metadata.get("title", title)
            except json.JSONDecodeError:
                pass

        # Get snippet
        snippet = ""
        if raw.content_text:
            snippet = raw.content_text[:2000]
            if len(raw.content_text) > 2000:
                snippet += "..."

        # Parse analysis for summary
        analysis_summary = None
        if analyzed and analyzed.analysis_result:
            try:
                analysis = json.loads(analyzed.analysis_result)
                analysis_summary = analysis.get("summary")
            except json.JSONDecodeError:
                pass

        formatted_results.append({
            "id": raw.id,
            "title": title,
            "source": src.name,
            "url": metadata.get("url") or metadata.get("video_url"),
            "date": raw.collected_at.strftime("%Y-%m-%d") if raw.collected_at else None,
            "type": raw.content_type,
            "snippet": snippet,
            "analysis_summary": analysis_summary,
            "themes": analyzed.key_themes.split(",") if analyzed and analyzed.key_themes else [],
            "sentiment": analyzed.sentiment if analyzed else None,
            "conviction": analyzed.conviction if analyzed else None
        })

    return {
        "results": formatted_results,
        "total_matches": total_matches,
        "query": q,
        "days_searched": days,
        "source_filter": source
    }


@router.get("/sources/{source_name}/view")
@limiter.limit(RATE_LIMITS["search"])
async def get_source_view(
    request: Request,
    source_name: str,
    topic: str = Query(..., min_length=1, description="Topic to query"),
    days: int = Query(14, ge=1, le=90, description="Days to look back"),
    db: AsyncSession = Depends(get_async_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Get a specific source's current view on a topic.

    Searches content from the specified source mentioning the topic
    and aggregates sentiment/conviction to determine the overall view.

    Args:
        source_name: Source name (e.g., "42macro", "discord")
        topic: Topic to query (e.g., "gold", "volatility", "equities")
        days: Number of days to look back (default 14)

    Returns:
        Dictionary with source's view on the topic
    """
    # PRD-037/046: Sanitize topic query and source name
    topic = sanitize_search_query(topic)
    safe_source_name = sanitize_search_query(source_name) if source_name else ""

    # Calculate cutoff date
    cutoff = datetime.utcnow() - timedelta(days=days)
    search_pattern = f"%{topic}%"

    # Find the source (PRD-046: sanitized)
    source_result = await db.execute(
        select(Source).where(Source.name.ilike(f"%{safe_source_name}%"))
    )
    source = source_result.scalar_one_or_none()

    if not source:
        return {
            "source": source_name,  # Return original for display
            "topic": topic,
            "current_view": None,
            "message": f"Source '{source_name}' not found",
            "related_content": []
        }

    # Query content mentioning the topic
    stmt = (
        select(RawContent, AnalyzedContent)
        .outerjoin(AnalyzedContent, RawContent.id == AnalyzedContent.raw_content_id)
        .where(
            RawContent.source_id == source.id,
            RawContent.collected_at >= cutoff
        )
        .where(
            (RawContent.content_text.ilike(search_pattern)) |
            (RawContent.json_metadata.ilike(search_pattern)) |
            (AnalyzedContent.key_themes.ilike(search_pattern))
        )
        .order_by(desc(RawContent.collected_at))
        .limit(10)
    )

    result = await db.execute(stmt)
    results = result.all()

    if not results:
        return {
            "source": source.name,
            "topic": topic,
            "current_view": None,
            "message": f"No content found from {source.name} about {topic} in the last {days} days",
            "related_content": []
        }

    # Analyze results to determine current view
    sentiments = []
    convictions = []
    related_content = []
    last_mentioned = None
    context_snippets = []

    for raw, analyzed in results:
        # Parse metadata
        metadata = {}
        if raw.json_metadata:
            try:
                metadata = json.loads(raw.json_metadata)
            except json.JSONDecodeError:
                pass

        # Collect sentiment and conviction
        if analyzed and analyzed.sentiment is not None:
            sentiments.append(analyzed.sentiment)
        if analyzed and analyzed.conviction is not None:
            convictions.append(analyzed.conviction)

        # Track last mentioned
        if raw.collected_at:
            if last_mentioned is None or raw.collected_at > last_mentioned:
                last_mentioned = raw.collected_at

        # Extract context snippets containing the topic
        if raw.content_text:
            sentences = raw.content_text.replace("\n", " ").split(".")
            for sentence in sentences:
                if topic.lower() in sentence.lower() and len(sentence.strip()) > 20:
                    context_snippets.append(sentence.strip() + ".")
                    break

        # Parse analysis for summary
        summary = None
        if analyzed and analyzed.analysis_result:
            try:
                analysis = json.loads(analyzed.analysis_result)
                summary = analysis.get("summary")
            except json.JSONDecodeError:
                pass

        related_content.append({
            "title": metadata.get("title", f"{source.name} content"),
            "date": raw.collected_at.strftime("%Y-%m-%d") if raw.collected_at else None,
            "type": raw.content_type,
            "themes": analyzed.key_themes.split(",") if analyzed and analyzed.key_themes else [],
            "summary": summary,
            "tickers": analyzed.tickers_mentioned.split(",") if analyzed and analyzed.tickers_mentioned else []
        })

    # Determine current view based on average sentiment
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else None
    avg_conviction = sum(convictions) / len(convictions) if convictions else None

    current_view = "unclear"
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

    # Build context from snippets
    context = " ".join(context_snippets[:3]) if context_snippets else None

    return {
        "source": source.name,
        "topic": topic,
        "current_view": current_view,
        "avg_sentiment": round(avg_sentiment, 2) if avg_sentiment else None,
        "avg_conviction": round(avg_conviction, 2) if avg_conviction else None,
        "last_mentioned": last_mentioned.strftime("%Y-%m-%d") if last_mentioned else None,
        "context": context,
        "mentions_count": len(results),
        "related_content": related_content[:5]
    }


@router.get("/themes/aggregated")
@limiter.limit(RATE_LIMITS["search"])
async def get_aggregated_themes(
    request: Request,
    active_only: bool = Query(True, description="Only include themes from recent content"),
    min_sources: int = Query(1, ge=1, le=10, description="Minimum number of sources"),
    days: int = Query(7, ge=1, le=90, description="Days to look back for active themes"),
    db: AsyncSession = Depends(get_async_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Get aggregated themes from analyzed content.

    This endpoint aggregates themes directly from analyzed_content records
    rather than the Theme table. Useful for getting a real-time view of
    what themes are being discussed.

    Args:
        active_only: Only include themes from recent content (default True)
        min_sources: Minimum number of sources mentioning theme (default 1)
        days: Days to look back for active themes (default 7)

    Returns:
        Dictionary with aggregated themes and metadata
    """
    # Calculate cutoff
    if active_only:
        cutoff = datetime.utcnow() - timedelta(days=days)
    else:
        cutoff = datetime(1970, 1, 1)

    # Query analyzed content with themes
    stmt = (
        select(AnalyzedContent, RawContent, Source)
        .join(RawContent, AnalyzedContent.raw_content_id == RawContent.id)
        .join(Source, RawContent.source_id == Source.id)
        .where(
            AnalyzedContent.analyzed_at >= cutoff,
            AnalyzedContent.key_themes.isnot(None),
            AnalyzedContent.key_themes != ""
        )
        .order_by(desc(AnalyzedContent.analyzed_at))
    )

    result = await db.execute(stmt)
    results = result.all()

    # Aggregate themes across sources
    theme_data = {}

    for analyzed, raw, source in results:
        themes = analyzed.key_themes.split(",") if analyzed.key_themes else []

        for theme in themes:
            theme = theme.strip()
            if not theme:
                continue

            if theme not in theme_data:
                theme_data[theme] = {
                    "name": theme,
                    "sources": set(),
                    "first_seen": analyzed.analyzed_at,
                    "last_seen": analyzed.analyzed_at,
                    "mention_count": 0,
                    "sentiments": [],
                    "convictions": []
                }

            theme_data[theme]["sources"].add(source.name)
            theme_data[theme]["mention_count"] += 1

            if analyzed.analyzed_at < theme_data[theme]["first_seen"]:
                theme_data[theme]["first_seen"] = analyzed.analyzed_at
            if analyzed.analyzed_at > theme_data[theme]["last_seen"]:
                theme_data[theme]["last_seen"] = analyzed.analyzed_at

            if analyzed.sentiment is not None:
                try:
                    theme_data[theme]["sentiments"].append(float(analyzed.sentiment))
                except (ValueError, TypeError):
                    pass
            if analyzed.conviction is not None:
                try:
                    theme_data[theme]["convictions"].append(float(analyzed.conviction))
                except (ValueError, TypeError):
                    pass

    # Filter by min_sources and format output
    themes_list = []
    for theme, data in theme_data.items():
        if len(data["sources"]) >= min_sources:
            # Calculate averages
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
                "first_seen": data["first_seen"].strftime("%Y-%m-%d") if data["first_seen"] else None,
                "last_seen": data["last_seen"].strftime("%Y-%m-%d") if data["last_seen"] else None,
                "avg_sentiment": round(avg_sentiment, 2) if avg_sentiment else None,
                "avg_conviction": round(avg_conviction, 2) if avg_conviction else None,
                "conviction_trend": conviction_trend
            })

    # Sort by mention count
    themes_list.sort(key=lambda x: x["mention_count"], reverse=True)

    return {
        "themes": themes_list,
        "total_themes": len(themes_list),
        "active_only": active_only,
        "min_sources": min_sources,
        "days": days
    }


@router.get("/recent/{source_name}")
@limiter.limit(RATE_LIMITS["search"])
async def get_recent_from_source(
    request: Request,
    source_name: str,
    days: int = Query(3, ge=1, le=30, description="Days to look back"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    limit: int = Query(20, ge=1, le=100, description="Maximum items to return"),
    db: AsyncSession = Depends(get_async_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Get recent content from a specific source.

    Args:
        source_name: Source name (e.g., "discord", "42macro")
        days: Number of days to look back (default 3)
        content_type: Optional filter by content type ("video", "pdf", "text", "image")
        limit: Maximum items to return (default 20)

    Returns:
        Dictionary with recent items from the source
    """
    # PRD-046: Sanitize source name
    safe_source_name = sanitize_search_query(source_name) if source_name else ""
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Find the source (PRD-046: sanitized)
    source_result = await db.execute(
        select(Source).where(Source.name.ilike(f"%{safe_source_name}%"))
    )
    source = source_result.scalar_one_or_none()

    if not source:
        return {
            "source": source_name,  # Return original for display
            "items": [],
            "count": 0,
            "days": days,
            "message": f"Source '{source_name}' not found"
        }

    # Build query
    stmt = (
        select(RawContent, AnalyzedContent)
        .outerjoin(AnalyzedContent, RawContent.id == AnalyzedContent.raw_content_id)
        .where(
            RawContent.source_id == source.id,
            RawContent.collected_at >= cutoff
        )
    )

    # Apply content type filter
    if content_type:
        stmt = stmt.where(RawContent.content_type == content_type)

    # Order by recency and limit
    stmt = stmt.order_by(desc(RawContent.collected_at)).limit(limit)

    result = await db.execute(stmt)
    results = result.all()

    # Format results
    items = []
    for raw, analyzed in results:
        # Parse metadata
        metadata = {}
        if raw.json_metadata:
            try:
                metadata = json.loads(raw.json_metadata)
            except json.JSONDecodeError:
                pass

        # Parse analysis result for summary
        summary = None
        if analyzed and analyzed.analysis_result:
            try:
                analysis = json.loads(analyzed.analysis_result)
                summary = analysis.get("summary")
            except json.JSONDecodeError:
                pass

        if not summary and raw.content_text:
            summary = raw.content_text[:1500]
            if len(raw.content_text) > 1500:
                summary += "..."

        items.append({
            "id": raw.id,
            "title": metadata.get("title", f"{source.name} content"),
            "type": raw.content_type,
            "date": raw.collected_at.strftime("%Y-%m-%d") if raw.collected_at else None,
            "datetime": raw.collected_at.isoformat() if raw.collected_at else None,
            "summary": summary,
            "themes": analyzed.key_themes.split(",") if analyzed and analyzed.key_themes else [],
            "sentiment": analyzed.sentiment if analyzed else None,
            "conviction": analyzed.conviction if analyzed else None,
            "url": metadata.get("url") or metadata.get("video_url")
        })

    return {
        "source": source.name,
        "items": items,
        "count": len(items),
        "days": days,
        "content_type_filter": content_type
    }
