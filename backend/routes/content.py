"""
Content Detail Routes

API endpoint for retrieving full content by ID, including
complete transcript text and parsed analysis results.

Used by MCP get_content_detail tool to drill into specific content
after finding items via search_research.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

from backend.models import (
    get_async_db,
    RawContent,
    AnalyzedContent,
    Source
)
from backend.utils.auth import verify_jwt_or_basic
from backend.utils.rate_limiter import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)
router = APIRouter()


def _split_csv(value: str) -> list:
    """Split comma-separated string, filtering out empty strings."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


@router.get("/{content_id}")
@limiter.limit(RATE_LIMITS["search"])
async def get_content_detail(
    request: Request,
    content_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Get full content detail by ID.

    Returns complete content text (no truncation), parsed analysis results,
    and all metadata. Use after search_research to drill into specific items.

    Args:
        content_id: RawContent ID

    Returns:
        Full content with analysis, metadata, and denormalized fields
    """
    # Query raw content
    result = await db.execute(
        select(RawContent).where(RawContent.id == content_id)
    )
    raw = result.scalar_one_or_none()

    if not raw:
        raise HTTPException(status_code=404, detail=f"Content {content_id} not found")

    # Get source
    src_result = await db.execute(
        select(Source).where(Source.id == raw.source_id)
    )
    source = src_result.scalar_one_or_none()

    # Get analyzed content
    analyzed_result = await db.execute(
        select(AnalyzedContent).where(AnalyzedContent.raw_content_id == raw.id)
    )
    analyzed = analyzed_result.scalar_one_or_none()

    # Parse metadata
    metadata = {}
    if raw.json_metadata:
        try:
            metadata = json.loads(raw.json_metadata)
        except json.JSONDecodeError:
            pass

    # Parse analysis result
    analysis_data = {}
    if analyzed and analyzed.analysis_result:
        try:
            parsed = json.loads(analyzed.analysis_result) if isinstance(analyzed.analysis_result, str) else analyzed.analysis_result
            if isinstance(parsed, dict):
                analysis_data = parsed
        except (json.JSONDecodeError, TypeError):
            pass

    source_name = source.name if source else "unknown"

    # Build response
    response = {
        "id": raw.id,
        "source": source_name,
        "title": metadata.get("title", f"{source_name} content"),
        "url": metadata.get("url") or metadata.get("video_url"),
        "content_type": raw.content_type,
        "collected_at": raw.collected_at.isoformat() if raw.collected_at else None,
        "content_text": raw.content_text or "",
        "content_length": len(raw.content_text) if raw.content_text else 0,
        "metadata": metadata,
        "analysis": {
            "summary": analysis_data.get("summary"),
            "key_quotes": analysis_data.get("key_quotes", []),
            "catalysts": analysis_data.get("catalysts", []),
            "falsification_criteria": analysis_data.get("falsification_criteria", []),
        },
        "themes": _split_csv(analyzed.key_themes) if analyzed else [],
        "tickers": _split_csv(analyzed.tickers_mentioned) if analyzed else [],
        "sentiment": analyzed.sentiment if analyzed else None,
        "conviction": analyzed.conviction if analyzed else None,
        "time_horizon": analyzed.time_horizon if analyzed else None,
        "analyzed_at": analyzed.analyzed_at.isoformat() if analyzed and analyzed.analyzed_at else None,
    }

    return response
