"""
Dashboard Routes

API endpoints for web dashboard pages.
Provides data for Today's View, Theme Tracker, Source Browser, Confluence Matrix, and Historical View.

Security (PRD-015):
- All endpoints require HTTP Basic Auth
- Rate limited to prevent abuse
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta
import json

from backend.models import (
    get_db,
    Theme,
    AnalyzedContent,
    ConfluenceScore,
    ThemeEvidence,
    BayesianUpdate,
    Source,
    RawContent
)
from backend.utils.auth import verify_credentials
from backend.utils.rate_limiter import limiter, RATE_LIMITS

router = APIRouter()


# ============================================================================
# Today's View Endpoints
# ============================================================================

@router.get("/today")
@limiter.limit(RATE_LIMITS["default"])
async def get_today_view(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Get data for Today's View dashboard page.

    Returns:
    - High-conviction ideas (score >=7/10)
    - Latest updates from each source
    - Recent confluence scores
    """
    # High-conviction themes (conviction >=0.75)
    high_conviction_themes = db.query(Theme).filter(
        Theme.current_conviction >= 0.75,
        Theme.status == 'active'
    ).order_by(desc(Theme.current_conviction)).limit(5).all()

    # Latest updates from each source (last 24 hours)
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    latest_updates = []

    sources = db.query(Source).filter(Source.active == True).all()
    for source in sources:
        latest_content = db.query(RawContent).filter(
            RawContent.source_id == source.id,
            RawContent.collected_at >= twenty_four_hours_ago
        ).order_by(desc(RawContent.collected_at)).first()

        if latest_content:
            latest_updates.append({
                "source": source.name,
                "content_type": latest_content.content_type,
                "collected_at": latest_content.collected_at.isoformat() if latest_content.collected_at else None,
                "url": latest_content.url,
                "id": latest_content.id
            })

    # Recent high-scoring confluence scores (last 7 days, score >=7)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    high_scores = db.query(ConfluenceScore).filter(
        ConfluenceScore.total_score >= 7,
        ConfluenceScore.scored_at >= seven_days_ago
    ).order_by(desc(ConfluenceScore.total_score), desc(ConfluenceScore.scored_at)).limit(10).all()

    high_scoring_content = []
    for score in high_scores:
        analyzed = db.query(AnalyzedContent).filter(
            AnalyzedContent.id == score.analyzed_content_id
        ).first()

        if analyzed:
            raw = db.query(RawContent).filter(RawContent.id == analyzed.raw_content_id).first()
            source = db.query(Source).filter(Source.id == raw.source_id).first() if raw else None

            high_scoring_content.append({
                "id": score.id,
                "source": source.name if source else "unknown",
                "core_score": score.core_total,
                "total_score": score.total_score,
                "meets_threshold": score.meets_threshold,
                "scored_at": score.scored_at.isoformat() if score.scored_at else None,
                "key_themes": analyzed.key_themes.split(',') if analyzed.key_themes else [],
                "sentiment": analyzed.sentiment,
                "conviction": analyzed.conviction
            })

    return {
        "high_conviction_themes": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "conviction": round(t.current_conviction, 3),
                "evidence_count": t.evidence_count,
                "first_mentioned": t.first_mentioned_at.isoformat() if t.first_mentioned_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None
            }
            for t in high_conviction_themes
        ],
        "latest_updates": latest_updates,
        "high_scoring_content": high_scoring_content,
        "summary": {
            "active_themes": db.query(Theme).filter(Theme.status == 'active').count(),
            "analyses_last_24h": db.query(AnalyzedContent).filter(
                AnalyzedContent.analyzed_at >= twenty_four_hours_ago
            ).count(),
            "high_conviction_count": len(high_conviction_themes)
        }
    }


# ============================================================================
# Theme Tracker Endpoints
# ============================================================================

@router.get("/themes")
@limiter.limit(RATE_LIMITS["default"])
async def get_all_themes(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status: active, acted_upon, invalidated"),
    min_conviction: Optional[float] = Query(None, description="Minimum conviction threshold"),
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Get all themes with optional filters.

    Query params:
    - status: Filter by theme status
    - min_conviction: Minimum conviction threshold (0.0-1.0)
    """
    query = db.query(Theme)

    if status:
        query = query.filter(Theme.status == status)

    if min_conviction is not None:
        query = query.filter(Theme.current_conviction >= min_conviction)

    themes = query.order_by(desc(Theme.current_conviction)).all()

    result = []
    for theme in themes:
        # Get evidence count
        evidence_count = db.query(ThemeEvidence).filter(
            ThemeEvidence.theme_id == theme.id,
            ThemeEvidence.supports_theme == True
        ).count()

        # Get latest Bayesian update
        latest_update = db.query(BayesianUpdate).filter(
            BayesianUpdate.theme_id == theme.id
        ).order_by(desc(BayesianUpdate.updated_at)).first()

        result.append({
            "id": theme.id,
            "name": theme.name,
            "description": theme.description,
            "conviction": round(theme.current_conviction, 3),
            "confidence_interval": [
                round(theme.confidence_interval_low, 3) if theme.confidence_interval_low else None,
                round(theme.confidence_interval_high, 3) if theme.confidence_interval_high else None
            ],
            "status": theme.status,
            "evidence_count": evidence_count,
            "first_mentioned": theme.first_mentioned_at.isoformat() if theme.first_mentioned_at else None,
            "updated_at": theme.updated_at.isoformat() if theme.updated_at else None,
            "last_update": {
                "prior": round(latest_update.prior_conviction, 3) if latest_update else None,
                "posterior": round(latest_update.posterior_conviction, 3) if latest_update else None,
                "date": latest_update.updated_at.isoformat() if latest_update else None
            } if latest_update else None
        })

    return result


@router.get("/themes/{theme_id}")
@limiter.limit(RATE_LIMITS["default"])
async def get_theme_detail(
    request: Request,
    theme_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Get detailed information about a specific theme.

    Includes:
    - Theme metadata
    - All supporting evidence
    - Bayesian update history
    - Conviction trend over time
    """
    theme = db.query(Theme).filter(Theme.id == theme_id).first()
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    # Get all evidence
    evidence_items = db.query(ThemeEvidence).filter(
        ThemeEvidence.theme_id == theme_id
    ).order_by(desc(ThemeEvidence.added_at)).all()

    evidence = []
    for ev in evidence_items:
        analyzed = db.query(AnalyzedContent).filter(AnalyzedContent.id == ev.analyzed_content_id).first()
        if analyzed:
            raw = db.query(RawContent).filter(RawContent.id == analyzed.raw_content_id).first()
            source = db.query(Source).filter(Source.id == raw.source_id).first() if raw else None

            evidence.append({
                "id": ev.id,
                "source": source.name if source else "unknown",
                "supports_theme": ev.supports_theme,
                "evidence_strength": round(ev.evidence_strength, 3),
                "added_at": ev.added_at.isoformat() if ev.added_at else None,
                "key_themes": analyzed.key_themes.split(',') if analyzed.key_themes else [],
                "sentiment": analyzed.sentiment,
                "conviction": analyzed.conviction,
                "analyzed_at": analyzed.analyzed_at.isoformat() if analyzed.analyzed_at else None
            })

    # Get Bayesian update history
    updates = db.query(BayesianUpdate).filter(
        BayesianUpdate.theme_id == theme_id
    ).order_by(BayesianUpdate.updated_at).all()

    bayesian_history = [
        {
            "prior": round(u.prior_conviction, 3),
            "posterior": round(u.posterior_conviction, 3),
            "date": u.updated_at.isoformat() if u.updated_at else None,
            "reason": u.update_reason
        }
        for u in updates
    ]

    return {
        "id": theme.id,
        "name": theme.name,
        "description": theme.description,
        "conviction": round(theme.current_conviction, 3),
        "confidence_interval": [
            round(theme.confidence_interval_low, 3) if theme.confidence_interval_low else None,
            round(theme.confidence_interval_high, 3) if theme.confidence_interval_high else None
        ],
        "status": theme.status,
        "first_mentioned": theme.first_mentioned_at.isoformat() if theme.first_mentioned_at else None,
        "created_at": theme.created_at.isoformat() if theme.created_at else None,
        "updated_at": theme.updated_at.isoformat() if theme.updated_at else None,
        "evidence": evidence,
        "bayesian_history": bayesian_history,
        "metadata": json.loads(theme.json_metadata) if theme.json_metadata else {}
    }


@router.post("/themes/{theme_id}/status")
@limiter.limit(RATE_LIMITS["default"])
async def update_theme_status(
    request: Request,
    theme_id: int,
    status: str = Query(..., description="New status: active, acted_upon, invalidated, archived"),
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Update theme status (e.g., mark as acted upon or invalidated).
    """
    theme = db.query(Theme).filter(Theme.id == theme_id).first()
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    valid_statuses = ['active', 'acted_upon', 'invalidated', 'archived']
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

    theme.status = status
    theme.updated_at = datetime.utcnow()
    db.commit()

    return {
        "id": theme.id,
        "name": theme.name,
        "status": theme.status,
        "updated_at": theme.updated_at.isoformat()
    }


# ============================================================================
# Source Browser Endpoints
# ============================================================================

@router.get("/sources")
@limiter.limit(RATE_LIMITS["default"])
async def get_all_sources(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """Get list of all sources with recent activity stats."""
    sources = db.query(Source).all()

    result = []
    for source in sources:
        # Count content items
        total_content = db.query(RawContent).filter(RawContent.source_id == source.id).count()

        # Get latest collection time
        latest = db.query(RawContent).filter(
            RawContent.source_id == source.id
        ).order_by(desc(RawContent.collected_at)).first()

        # Count analyzed items
        analyzed_count = db.query(AnalyzedContent).join(RawContent).filter(
            RawContent.source_id == source.id
        ).count()

        result.append({
            "id": source.id,
            "name": source.name,
            "type": source.type,
            "active": source.active,
            "total_items": total_content,
            "analyzed_items": analyzed_count,
            "last_collected": latest.collected_at.isoformat() if latest and latest.collected_at else None,
            "created_at": source.created_at.isoformat() if source.created_at else None
        })

    return result


@router.get("/sources/{source_name}")
@limiter.limit(RATE_LIMITS["search"])
async def get_source_content(
    request: Request,
    source_name: str,
    limit: int = Query(50, description="Number of items to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Get content from a specific source with pagination.

    Query params:
    - limit: Number of items (default: 50)
    - offset: Pagination offset (default: 0)
    """
    source = db.query(Source).filter(Source.name == source_name).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Get content items
    content_items = db.query(RawContent).filter(
        RawContent.source_id == source.id
    ).order_by(desc(RawContent.collected_at)).limit(limit).offset(offset).all()

    result = []
    for item in content_items:
        # Get analysis if exists
        analyzed = db.query(AnalyzedContent).filter(
            AnalyzedContent.raw_content_id == item.id
        ).first()

        # Get confluence score if exists
        confluence = None
        if analyzed:
            confluence_score = db.query(ConfluenceScore).filter(
                ConfluenceScore.analyzed_content_id == analyzed.id
            ).first()
            if confluence_score:
                confluence = {
                    "core_score": confluence_score.core_total,
                    "total_score": confluence_score.total_score,
                    "meets_threshold": confluence_score.meets_threshold
                }

        result.append({
            "id": item.id,
            "content_type": item.content_type,
            "collected_at": item.collected_at.isoformat() if item.collected_at else None,
            "url": item.url,
            "file_path": item.file_path,
            "processed": item.processed,
            "analysis": {
                "agent_type": analyzed.agent_type if analyzed else None,
                "key_themes": analyzed.key_themes.split(',') if analyzed and analyzed.key_themes else [],
                "sentiment": analyzed.sentiment if analyzed else None,
                "conviction": analyzed.conviction if analyzed else None
            } if analyzed else None,
            "confluence": confluence
        })

    # Get total count for pagination
    total_count = db.query(RawContent).filter(RawContent.source_id == source.id).count()

    return {
        "source": {
            "id": source.id,
            "name": source.name,
            "type": source.type
        },
        "content": result,
        "pagination": {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
    }


# ============================================================================
# Confluence Matrix Endpoint
# ============================================================================

@router.get("/matrix")
@limiter.limit(RATE_LIMITS["search"])
async def get_confluence_matrix(
    request: Request,
    days: int = Query(30, description="Number of days to include"),
    min_score: int = Query(4, description="Minimum total score to include"),
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Get confluence matrix data (heatmap of pillar scores).

    Returns matrix where:
    - Rows = themes or content pieces
    - Columns = 7 pillars
    - Values = scores (0, 1, 2)

    Query params:
    - days: How many days back to include (default: 30)
    - min_score: Minimum total score to include (default: 4)
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get confluence scores
    scores = db.query(ConfluenceScore).filter(
        ConfluenceScore.scored_at >= cutoff_date,
        ConfluenceScore.total_score >= min_score
    ).order_by(desc(ConfluenceScore.total_score)).limit(50).all()

    matrix_data = []
    for score in scores:
        analyzed = db.query(AnalyzedContent).filter(
            AnalyzedContent.id == score.analyzed_content_id
        ).first()

        if analyzed:
            raw = db.query(RawContent).filter(RawContent.id == analyzed.raw_content_id).first()
            source = db.query(Source).filter(Source.id == raw.source_id).first() if raw else None

            # Extract primary theme (first key theme)
            themes = analyzed.key_themes.split(',') if analyzed.key_themes else []
            primary_theme = themes[0].strip() if themes else "Unknown"

            matrix_data.append({
                "id": score.id,
                "theme": primary_theme,
                "source": source.name if source else "unknown",
                "scored_at": score.scored_at.isoformat() if score.scored_at else None,
                "pillars": {
                    "macro": score.macro_score,
                    "fundamentals": score.fundamentals_score,
                    "valuation": score.valuation_score,
                    "positioning": score.positioning_score,
                    "policy": score.policy_score,
                    "price_action": score.price_action_score,
                    "options_vol": score.options_vol_score
                },
                "totals": {
                    "core": score.core_total,
                    "total": score.total_score,
                    "meets_threshold": score.meets_threshold
                }
            })

    return {
        "matrix": matrix_data,
        "filters": {
            "days": days,
            "min_score": min_score,
            "count": len(matrix_data)
        },
        "pillar_names": ["macro", "fundamentals", "valuation", "positioning", "policy", "price_action", "options_vol"]
    }


# ============================================================================
# Historical View Endpoint
# ============================================================================

@router.get("/historical/{theme_id}")
@limiter.limit(RATE_LIMITS["search"])
async def get_historical_data(
    request: Request,
    theme_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Get historical data for a specific theme.

    Returns:
    - Conviction line chart data over time
    - Evidence timeline (when new data arrived)
    - Bayesian update log
    """
    theme = db.query(Theme).filter(Theme.id == theme_id).first()
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    # Get Bayesian updates (conviction over time)
    updates = db.query(BayesianUpdate).filter(
        BayesianUpdate.theme_id == theme_id
    ).order_by(BayesianUpdate.updated_at).all()

    conviction_timeline = []
    if updates:
        # Add initial point (prior of first update)
        conviction_timeline.append({
            "date": updates[0].updated_at.isoformat() if updates[0].updated_at else None,
            "conviction": round(updates[0].prior_conviction, 3)
        })

        # Add all posteriors
        for update in updates:
            conviction_timeline.append({
                "date": update.updated_at.isoformat() if update.updated_at else None,
                "conviction": round(update.posterior_conviction, 3),
                "reason": update.update_reason
            })

    # Get evidence timeline
    evidence_items = db.query(ThemeEvidence).filter(
        ThemeEvidence.theme_id == theme_id
    ).order_by(ThemeEvidence.added_at).all()

    evidence_timeline = []
    for ev in evidence_items:
        analyzed = db.query(AnalyzedContent).filter(AnalyzedContent.id == ev.analyzed_content_id).first()
        if analyzed:
            raw = db.query(RawContent).filter(RawContent.id == analyzed.raw_content_id).first()
            source = db.query(Source).filter(Source.id == raw.source_id).first() if raw else None

            evidence_timeline.append({
                "date": ev.added_at.isoformat() if ev.added_at else None,
                "source": source.name if source else "unknown",
                "supports": ev.supports_theme,
                "strength": round(ev.evidence_strength, 3),
                "sentiment": analyzed.sentiment,
                "conviction": analyzed.conviction
            })

    return {
        "theme": {
            "id": theme.id,
            "name": theme.name,
            "description": theme.description,
            "current_conviction": round(theme.current_conviction, 3),
            "status": theme.status
        },
        "conviction_timeline": conviction_timeline,
        "evidence_timeline": evidence_timeline,
        "bayesian_updates": [
            {
                "date": u.updated_at.isoformat() if u.updated_at else None,
                "prior": round(u.prior_conviction, 3),
                "posterior": round(u.posterior_conviction, 3),
                "delta": round(u.posterior_conviction - u.prior_conviction, 3),
                "reason": u.update_reason
            }
            for u in updates
        ],
        "summary": {
            "total_updates": len(updates),
            "total_evidence": len(evidence_items),
            "supporting_evidence": sum(1 for e in evidence_items if e.supports_theme),
            "contradicting_evidence": sum(1 for e in evidence_items if not e.supports_theme),
            "first_mentioned": theme.first_mentioned_at.isoformat() if theme.first_mentioned_at else None
        }
    }


# ============================================================================
# Stats Endpoint
# ============================================================================

@router.get("/stats")
@limiter.limit(RATE_LIMITS["default"])
async def get_dashboard_stats(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """Get overall dashboard statistics."""
    return {
        "sources": {
            "total": db.query(Source).count(),
            "active": db.query(Source).filter(Source.active == True).count()
        },
        "content": {
            "total_raw": db.query(RawContent).count(),
            "analyzed": db.query(AnalyzedContent).count(),
            "scored": db.query(ConfluenceScore).count()
        },
        "themes": {
            "total": db.query(Theme).count(),
            "active": db.query(Theme).filter(Theme.status == 'active').count(),
            "high_conviction": db.query(Theme).filter(
                Theme.current_conviction >= 0.75,
                Theme.status == 'active'
            ).count()
        },
        "recent_activity": {
            "last_24h_collected": db.query(RawContent).filter(
                RawContent.collected_at >= datetime.utcnow() - timedelta(hours=24)
            ).count(),
            "last_24h_analyzed": db.query(AnalyzedContent).filter(
                AnalyzedContent.analyzed_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
        }
    }
