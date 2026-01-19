"""
Synthesis Quality Routes (PRD-044)

API endpoints for synthesis quality scores and evaluation data.
Provides access to quality metrics, trends, and flagged issues.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
from datetime import datetime, timedelta
import json
import logging

from backend.models import (
    get_db,
    Synthesis,
    SynthesisQualityScore
)
from backend.utils.auth import verify_jwt_or_basic
from backend.utils.rate_limiter import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{synthesis_id}")
@limiter.limit(RATE_LIMITS["default"])
async def get_quality_score(
    request: Request,
    synthesis_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Get quality score for a specific synthesis.

    Returns full quality evaluation including criterion scores, flags, and suggestions.
    """
    quality = db.query(SynthesisQualityScore).filter(
        SynthesisQualityScore.synthesis_id == synthesis_id
    ).first()

    if not quality:
        raise HTTPException(
            status_code=404,
            detail=f"Quality score not found for synthesis {synthesis_id}"
        )

    return _format_quality_response(quality)


@router.get("/latest")
@limiter.limit(RATE_LIMITS["default"])
async def get_latest_quality(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Get quality score for the most recent synthesis.

    Returns full quality evaluation for the latest synthesis with quality data.
    """
    quality = db.query(SynthesisQualityScore).order_by(
        desc(SynthesisQualityScore.created_at)
    ).first()

    if not quality:
        return {
            "status": "not_found",
            "message": "No quality scores found. Generate a synthesis first."
        }

    return _format_quality_response(quality)


@router.get("/history")
@limiter.limit(RATE_LIMITS["default"])
async def get_quality_history(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum quality score filter"),
    max_score: Optional[int] = Query(None, ge=0, le=100, description="Maximum quality score filter"),
    grade: Optional[str] = Query(None, description="Filter by grade (A+, A, A-, B+, etc.)"),
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Get quality score history.

    Returns a list of quality scores ordered by creation time, with optional filters.
    """
    query = db.query(SynthesisQualityScore)

    # Apply filters
    if min_score is not None:
        query = query.filter(SynthesisQualityScore.quality_score >= min_score)
    if max_score is not None:
        query = query.filter(SynthesisQualityScore.quality_score <= max_score)
    if grade:
        query = query.filter(SynthesisQualityScore.grade == grade)

    # Get total count before pagination
    total = query.count()

    # Apply pagination and ordering
    scores = query.order_by(
        desc(SynthesisQualityScore.created_at)
    ).offset(offset).limit(limit).all()

    return {
        "quality_scores": [_format_quality_response(q) for q in scores],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/flagged")
@limiter.limit(RATE_LIMITS["default"])
async def get_flagged_syntheses(
    request: Request,
    limit: int = Query(10, ge=1, le=50, description="Number of records to return"),
    severity: Optional[str] = Query(None, description="Filter by flag severity (low/medium/high)"),
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Get syntheses with quality flags (issues).

    Returns syntheses that have flags indicating quality issues.
    Flags are generated when criterion scores are 1 or below.
    """
    # Query scores that have flags (non-empty JSON array)
    query = db.query(SynthesisQualityScore).filter(
        SynthesisQualityScore.flags.isnot(None),
        SynthesisQualityScore.flags != "[]"
    )

    scores = query.order_by(
        desc(SynthesisQualityScore.created_at)
    ).limit(limit * 2).all()  # Get extra to filter by severity

    # Filter by severity if specified
    flagged_results = []
    for quality in scores:
        try:
            flags = json.loads(quality.flags) if quality.flags else []
            if not flags:
                continue

            # Filter by severity if specified
            if severity:
                flags = [f for f in flags if _get_flag_severity(f.get("score", 1)) == severity]
                if not flags:
                    continue

            flagged_results.append({
                "synthesis_id": quality.synthesis_id,
                "quality_score": quality.quality_score,
                "grade": quality.grade,
                "flags": flags,
                "created_at": quality.created_at.isoformat() if quality.created_at else None
            })

            if len(flagged_results) >= limit:
                break

        except json.JSONDecodeError:
            continue

    return {
        "flagged_syntheses": flagged_results,
        "count": len(flagged_results)
    }


@router.get("/trends")
@limiter.limit(RATE_LIMITS["default"])
async def get_quality_trends(
    request: Request,
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Get quality score trends over time.

    Returns aggregate statistics and trend data for quality scores.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    scores = db.query(SynthesisQualityScore).filter(
        SynthesisQualityScore.created_at >= cutoff
    ).order_by(SynthesisQualityScore.created_at).all()

    if not scores:
        return {
            "period_days": days,
            "total_evaluations": 0,
            "message": "No quality evaluations found in this period"
        }

    # Calculate statistics
    quality_scores = [s.quality_score for s in scores]
    avg_score = sum(quality_scores) / len(quality_scores)

    # Count grades
    grade_counts = {}
    for s in scores:
        grade_counts[s.grade] = grade_counts.get(s.grade, 0) + 1

    # Calculate criterion averages
    criterion_avgs = {
        "confluence_detection": sum(s.confluence_detection for s in scores) / len(scores),
        "evidence_preservation": sum(s.evidence_preservation for s in scores) / len(scores),
        "source_attribution": sum(s.source_attribution for s in scores) / len(scores),
        "youtube_channel_granularity": sum(s.youtube_channel_granularity for s in scores) / len(scores),
        "nuance_retention": sum(s.nuance_retention for s in scores) / len(scores),
        "actionability": sum(s.actionability for s in scores) / len(scores),
        "theme_continuity": sum(s.theme_continuity for s in scores) / len(scores)
    }

    # Find weakest and strongest criteria
    weakest = min(criterion_avgs, key=criterion_avgs.get)
    strongest = max(criterion_avgs, key=criterion_avgs.get)

    # Calculate trend (compare first half to second half)
    mid = len(scores) // 2
    if mid > 0:
        first_half_avg = sum(s.quality_score for s in scores[:mid]) / mid
        second_half_avg = sum(s.quality_score for s in scores[mid:]) / (len(scores) - mid)
        trend = "improving" if second_half_avg > first_half_avg else "declining" if second_half_avg < first_half_avg else "stable"
        trend_delta = round(second_half_avg - first_half_avg, 1)
    else:
        trend = "insufficient_data"
        trend_delta = 0

    return {
        "period_days": days,
        "total_evaluations": len(scores),
        "average_score": round(avg_score, 1),
        "min_score": min(quality_scores),
        "max_score": max(quality_scores),
        "grade_distribution": grade_counts,
        "criterion_averages": {k: round(v, 2) for k, v in criterion_avgs.items()},
        "weakest_criterion": weakest,
        "strongest_criterion": strongest,
        "trend": trend,
        "trend_delta": trend_delta
    }


def _format_quality_response(quality: SynthesisQualityScore) -> dict:
    """Format a quality score record for API response."""
    try:
        flags = json.loads(quality.flags) if quality.flags else []
    except json.JSONDecodeError:
        flags = []

    try:
        suggestions = json.loads(quality.prompt_suggestions) if quality.prompt_suggestions else []
    except json.JSONDecodeError:
        suggestions = []

    return {
        "synthesis_id": quality.synthesis_id,
        "quality_score": quality.quality_score,
        "grade": quality.grade,
        "criterion_scores": {
            "confluence_detection": quality.confluence_detection,
            "evidence_preservation": quality.evidence_preservation,
            "source_attribution": quality.source_attribution,
            "youtube_channel_granularity": quality.youtube_channel_granularity,
            "nuance_retention": quality.nuance_retention,
            "actionability": quality.actionability,
            "theme_continuity": quality.theme_continuity
        },
        "flags": flags,
        "prompt_suggestions": suggestions,
        "created_at": quality.created_at.isoformat() if quality.created_at else None
    }


def _get_flag_severity(score: int) -> str:
    """Determine flag severity based on criterion score."""
    if score == 0:
        return "high"
    elif score == 1:
        return "medium"
    return "low"
