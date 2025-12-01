"""
Confluence Routes

API endpoints for confluence scoring, theme tracking, and cross-reference analysis.
Provides the core investment research synthesis functionality.

Security (PRD-015):
- All endpoints require HTTP Basic Auth
- Rate limited to prevent abuse
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta
import json
import logging

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

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Confluence Score Endpoints
# ============================================================================

@router.get("/scores")
@limiter.limit(RATE_LIMITS["search"])
async def list_confluence_scores(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    min_score: Optional[int] = Query(None, ge=0, le=14),
    meets_threshold: Optional[bool] = None,
    source: Optional[str] = None,
    days: Optional[int] = Query(None, ge=1, le=365),
    user: str = Depends(verify_credentials)
):
    """
    List confluence scores with filtering options.

    Args:
        limit: Maximum number of results (default 50)
        offset: Pagination offset
        min_score: Minimum total score filter
        meets_threshold: Filter by threshold status
        source: Filter by source name
        days: Filter to last N days

    Returns:
        List of confluence scores with metadata
    """
    query = db.query(ConfluenceScore)

    # Apply filters
    if min_score is not None:
        query = query.filter(ConfluenceScore.total_score >= min_score)

    if meets_threshold is not None:
        query = query.filter(ConfluenceScore.meets_threshold == meets_threshold)

    if days is not None:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ConfluenceScore.scored_at >= cutoff)

    # Source filter requires join
    if source:
        query = query.join(
            AnalyzedContent,
            ConfluenceScore.analyzed_content_id == AnalyzedContent.id
        ).join(
            RawContent,
            AnalyzedContent.raw_content_id == RawContent.id
        ).join(
            Source,
            RawContent.source_id == Source.id
        ).filter(Source.name == source)

    # Get total count
    total = query.count()

    # Order and paginate
    scores = query.order_by(
        desc(ConfluenceScore.total_score),
        desc(ConfluenceScore.scored_at)
    ).offset(offset).limit(limit).all()

    # Build response
    results = []
    for score in scores:
        analyzed = db.query(AnalyzedContent).filter(
            AnalyzedContent.id == score.analyzed_content_id
        ).first()

        source_name = "unknown"
        if analyzed:
            raw = db.query(RawContent).filter(RawContent.id == analyzed.raw_content_id).first()
            if raw:
                src = db.query(Source).filter(Source.id == raw.source_id).first()
                source_name = src.name if src else "unknown"

        results.append({
            "id": score.id,
            "analyzed_content_id": score.analyzed_content_id,
            "source": source_name,
            "pillar_scores": {
                "macro": score.macro_score,
                "fundamentals": score.fundamentals_score,
                "valuation": score.valuation_score,
                "positioning": score.positioning_score,
                "policy": score.policy_score,
                "price_action": score.price_action_score,
                "options_vol": score.options_vol_score
            },
            "core_total": score.core_total,
            "total_score": score.total_score,
            "meets_threshold": score.meets_threshold,
            "scored_at": score.scored_at.isoformat() if score.scored_at else None,
            "key_themes": analyzed.key_themes.split(',') if analyzed and analyzed.key_themes else [],
            "sentiment": analyzed.sentiment if analyzed else None
        })

    return {
        "scores": results,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/scores/{score_id}")
@limiter.limit(RATE_LIMITS["default"])
async def get_confluence_score(
    request: Request,
    score_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Get detailed confluence score by ID.

    Args:
        score_id: Confluence score ID

    Returns:
        Complete confluence score with reasoning and falsification criteria
    """
    score = db.query(ConfluenceScore).filter(ConfluenceScore.id == score_id).first()

    if not score:
        raise HTTPException(status_code=404, detail="Confluence score not found")

    # Get related content
    analyzed = db.query(AnalyzedContent).filter(
        AnalyzedContent.id == score.analyzed_content_id
    ).first()

    source_name = "unknown"
    raw_content = None
    if analyzed:
        raw = db.query(RawContent).filter(RawContent.id == analyzed.raw_content_id).first()
        raw_content = raw
        if raw:
            src = db.query(Source).filter(Source.id == raw.source_id).first()
            source_name = src.name if src else "unknown"

    # Parse reasoning JSON
    reasoning = {}
    if score.reasoning:
        try:
            reasoning = json.loads(score.reasoning)
        except json.JSONDecodeError:
            reasoning = {"raw": score.reasoning}

    # Parse falsification criteria
    falsification = []
    if score.falsification_criteria:
        try:
            falsification = json.loads(score.falsification_criteria)
        except json.JSONDecodeError:
            falsification = [score.falsification_criteria]

    return {
        "id": score.id,
        "analyzed_content_id": score.analyzed_content_id,
        "source": source_name,
        "pillar_scores": {
            "macro": score.macro_score,
            "fundamentals": score.fundamentals_score,
            "valuation": score.valuation_score,
            "positioning": score.positioning_score,
            "policy": score.policy_score,
            "price_action": score.price_action_score,
            "options_vol": score.options_vol_score
        },
        "core_total": score.core_total,
        "total_score": score.total_score,
        "meets_threshold": score.meets_threshold,
        "reasoning": reasoning,
        "falsification_criteria": falsification,
        "scored_at": score.scored_at.isoformat() if score.scored_at else None,
        "analyzed_content": {
            "id": analyzed.id if analyzed else None,
            "agent_type": analyzed.agent_type if analyzed else None,
            "key_themes": analyzed.key_themes.split(',') if analyzed and analyzed.key_themes else [],
            "tickers": analyzed.tickers_mentioned.split(',') if analyzed and analyzed.tickers_mentioned else [],
            "sentiment": analyzed.sentiment if analyzed else None,
            "conviction": analyzed.conviction if analyzed else None,
            "time_horizon": analyzed.time_horizon if analyzed else None
        },
        "raw_content": {
            "id": raw_content.id if raw_content else None,
            "content_type": raw_content.content_type if raw_content else None,
            "url": raw_content.url if raw_content else None,
            "collected_at": raw_content.collected_at.isoformat() if raw_content and raw_content.collected_at else None
        } if raw_content else None
    }


@router.post("/score/{analyzed_content_id}")
@limiter.limit(RATE_LIMITS["synthesis"])
async def score_content(
    request: Request,
    analyzed_content_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Score analyzed content using the confluence scorer agent.

    Args:
        analyzed_content_id: ID of analyzed content to score

    Returns:
        Confluence score result or job status
    """
    # Check if analyzed content exists
    analyzed = db.query(AnalyzedContent).filter(
        AnalyzedContent.id == analyzed_content_id
    ).first()

    if not analyzed:
        raise HTTPException(status_code=404, detail="Analyzed content not found")

    # Check if already scored
    existing = db.query(ConfluenceScore).filter(
        ConfluenceScore.analyzed_content_id == analyzed_content_id
    ).first()

    if existing:
        return {
            "status": "already_scored",
            "score_id": existing.id,
            "total_score": existing.total_score,
            "meets_threshold": existing.meets_threshold
        }

    # Import scorer agent
    try:
        from agents.confluence_scorer import ConfluenceScorerAgent

        # Parse analysis result
        analysis_result = {}
        if analyzed.analysis_result:
            try:
                analysis_result = json.loads(analyzed.analysis_result)
            except json.JSONDecodeError:
                analysis_result = {"raw_text": analyzed.analysis_result}

        # Get source info
        raw = db.query(RawContent).filter(RawContent.id == analyzed.raw_content_id).first()
        source_name = "unknown"
        if raw:
            src = db.query(Source).filter(Source.id == raw.source_id).first()
            source_name = src.name if src else "unknown"

        # Add metadata to analysis result
        analysis_result["source"] = source_name
        analysis_result["content_type"] = raw.content_type if raw else "unknown"

        # Score content
        scorer = ConfluenceScorerAgent()
        result = scorer.analyze(analysis_result)

        # Save to database
        pillar_scores = result.get("pillar_scores", {})

        new_score = ConfluenceScore(
            analyzed_content_id=analyzed_content_id,
            macro_score=pillar_scores.get("macro", 0),
            fundamentals_score=pillar_scores.get("fundamentals", 0),
            valuation_score=pillar_scores.get("valuation", 0),
            positioning_score=pillar_scores.get("positioning", 0),
            policy_score=pillar_scores.get("policy", 0),
            price_action_score=pillar_scores.get("price_action", 0),
            options_vol_score=pillar_scores.get("options_vol", 0),
            core_total=result.get("core_total", 0),
            total_score=result.get("total_score", 0),
            meets_threshold=result.get("meets_threshold", False),
            reasoning=json.dumps(result.get("reasoning", {})),
            falsification_criteria=json.dumps(result.get("falsification_criteria", []))
        )

        db.add(new_score)
        db.commit()
        db.refresh(new_score)

        logger.info(f"Scored content {analyzed_content_id}: {new_score.total_score}/14")

        return {
            "status": "scored",
            "score_id": new_score.id,
            "pillar_scores": pillar_scores,
            "core_total": new_score.core_total,
            "total_score": new_score.total_score,
            "meets_threshold": new_score.meets_threshold,
            "confluence_level": result.get("confluence_level", "unknown"),
            "primary_thesis": result.get("primary_thesis", ""),
            "falsification_criteria": result.get("falsification_criteria", [])
        }

    except ImportError as e:
        logger.error(f"Failed to import confluence scorer: {e}")
        raise HTTPException(status_code=500, detail="Confluence scorer agent not available")
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")


# ============================================================================
# Theme Endpoints
# ============================================================================

@router.get("/themes")
@limiter.limit(RATE_LIMITS["default"])
async def list_themes(
    request: Request,
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, regex="^(active|acted_upon|invalidated|archived)$"),
    min_conviction: Optional[float] = Query(None, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: str = Depends(verify_credentials)
):
    """
    List investment themes with filtering.

    Args:
        status: Filter by theme status
        min_conviction: Minimum conviction threshold
        limit: Maximum results
        offset: Pagination offset

    Returns:
        List of themes with conviction data
    """
    query = db.query(Theme)

    if status:
        query = query.filter(Theme.status == status)

    if min_conviction is not None:
        query = query.filter(Theme.current_conviction >= min_conviction)

    total = query.count()

    themes = query.order_by(
        desc(Theme.current_conviction),
        desc(Theme.updated_at)
    ).offset(offset).limit(limit).all()

    results = []
    for theme in themes:
        # Get evidence count
        evidence_count = db.query(ThemeEvidence).filter(
            ThemeEvidence.theme_id == theme.id
        ).count()

        # Get supporting vs contradicting
        supporting = db.query(ThemeEvidence).filter(
            ThemeEvidence.theme_id == theme.id,
            ThemeEvidence.supports_theme == True
        ).count()

        results.append({
            "id": theme.id,
            "name": theme.name,
            "description": theme.description,
            "current_conviction": theme.current_conviction,
            "confidence_interval": [
                theme.confidence_interval_low,
                theme.confidence_interval_high
            ] if theme.confidence_interval_low else None,
            "status": theme.status,
            "first_mentioned_at": theme.first_mentioned_at.isoformat() if theme.first_mentioned_at else None,
            "evidence_count": evidence_count,
            "supporting_evidence": supporting,
            "contradicting_evidence": evidence_count - supporting,
            "updated_at": theme.updated_at.isoformat() if theme.updated_at else None
        })

    return {
        "themes": results,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/themes/{theme_id}")
@limiter.limit(RATE_LIMITS["default"])
async def get_theme(
    request: Request,
    theme_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Get detailed theme information with evidence and Bayesian history.

    Args:
        theme_id: Theme ID

    Returns:
        Complete theme data with evidence and conviction history
    """
    theme = db.query(Theme).filter(Theme.id == theme_id).first()

    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    # Get all evidence
    evidence_items = db.query(ThemeEvidence).filter(
        ThemeEvidence.theme_id == theme_id
    ).order_by(desc(ThemeEvidence.added_at)).all()

    evidence_list = []
    for ev in evidence_items:
        analyzed = db.query(AnalyzedContent).filter(
            AnalyzedContent.id == ev.analyzed_content_id
        ).first()

        source_name = "unknown"
        if analyzed:
            raw = db.query(RawContent).filter(RawContent.id == analyzed.raw_content_id).first()
            if raw:
                src = db.query(Source).filter(Source.id == raw.source_id).first()
                source_name = src.name if src else "unknown"

        evidence_list.append({
            "id": ev.id,
            "source": source_name,
            "supports_theme": ev.supports_theme,
            "evidence_strength": ev.evidence_strength,
            "added_at": ev.added_at.isoformat() if ev.added_at else None,
            "analyzed_content_id": ev.analyzed_content_id,
            "key_themes": analyzed.key_themes.split(',') if analyzed and analyzed.key_themes else []
        })

    # Get Bayesian update history
    updates = db.query(BayesianUpdate).filter(
        BayesianUpdate.theme_id == theme_id
    ).order_by(desc(BayesianUpdate.updated_at)).limit(20).all()

    update_history = [
        {
            "id": u.id,
            "prior": u.prior_conviction,
            "posterior": u.posterior_conviction,
            "reason": u.update_reason,
            "updated_at": u.updated_at.isoformat() if u.updated_at else None
        }
        for u in updates
    ]

    # Parse metadata
    metadata = {}
    if theme.json_metadata:
        try:
            metadata = json.loads(theme.json_metadata)
        except json.JSONDecodeError:
            pass

    return {
        "id": theme.id,
        "name": theme.name,
        "description": theme.description,
        "current_conviction": theme.current_conviction,
        "confidence_interval": [
            theme.confidence_interval_low,
            theme.confidence_interval_high
        ] if theme.confidence_interval_low else None,
        "status": theme.status,
        "first_mentioned_at": theme.first_mentioned_at.isoformat() if theme.first_mentioned_at else None,
        "prior_probability": theme.prior_probability,
        "evidence_count": theme.evidence_count,
        "evidence": evidence_list,
        "bayesian_history": update_history,
        "metadata": metadata,
        "created_at": theme.created_at.isoformat() if theme.created_at else None,
        "updated_at": theme.updated_at.isoformat() if theme.updated_at else None
    }


@router.patch("/themes/{theme_id}/status")
@limiter.limit(RATE_LIMITS["default"])
async def update_theme_status(
    request: Request,
    theme_id: int,
    status: str = Query(..., regex="^(active|acted_upon|invalidated|archived)$"),
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Update theme status.

    Args:
        theme_id: Theme ID
        status: New status value

    Returns:
        Updated theme
    """
    theme = db.query(Theme).filter(Theme.id == theme_id).first()

    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    theme.status = status
    theme.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(theme)

    logger.info(f"Updated theme {theme_id} status to {status}")

    return {
        "id": theme.id,
        "name": theme.name,
        "status": theme.status,
        "updated_at": theme.updated_at.isoformat()
    }


# ============================================================================
# Cross-Reference Endpoints
# ============================================================================

@router.post("/cross-reference")
@limiter.limit(RATE_LIMITS["synthesis"])
async def run_cross_reference(
    request: Request,
    db: Session = Depends(get_db),
    time_window_days: int = Query(7, ge=1, le=90),
    min_sources: int = Query(2, ge=1, le=6),
    user: str = Depends(verify_credentials)
):
    """
    Run cross-reference analysis on recent confluence scores.

    Args:
        time_window_days: Analysis time window in days
        min_sources: Minimum sources for confluence

    Returns:
        Cross-reference analysis results
    """
    try:
        from agents.cross_reference import CrossReferenceAgent

        # Get recent confluence scores
        cutoff = datetime.utcnow() - timedelta(days=time_window_days)

        scores = db.query(ConfluenceScore).filter(
            ConfluenceScore.scored_at >= cutoff
        ).all()

        if not scores:
            return {
                "status": "no_data",
                "message": f"No confluence scores found in the last {time_window_days} days"
            }

        # Build confluence score data for agent
        confluence_data = []
        for score in scores:
            analyzed = db.query(AnalyzedContent).filter(
                AnalyzedContent.id == score.analyzed_content_id
            ).first()

            source_name = "unknown"
            if analyzed:
                raw = db.query(RawContent).filter(RawContent.id == analyzed.raw_content_id).first()
                if raw:
                    src = db.query(Source).filter(Source.id == raw.source_id).first()
                    source_name = src.name if src else "unknown"

            # Parse reasoning for primary thesis
            primary_thesis = ""
            if score.reasoning:
                try:
                    reasoning = json.loads(score.reasoning)
                    primary_thesis = reasoning.get("primary_thesis", "")
                except json.JSONDecodeError:
                    pass

            confluence_data.append({
                "content_source": source_name,
                "scored_at": score.scored_at.isoformat() if score.scored_at else None,
                "core_total": score.core_total,
                "total_score": score.total_score,
                "meets_threshold": score.meets_threshold,
                "confluence_level": "strong" if score.meets_threshold else ("medium" if score.core_total >= 4 else "weak"),
                "primary_thesis": primary_thesis,
                "variant_view": "",
                "p_and_l_mechanism": "",
                "falsification_criteria": []
            })

        # Get historical themes
        historical_themes = []
        themes = db.query(Theme).filter(Theme.status == 'active').all()
        for theme in themes:
            historical_themes.append({
                "theme": theme.name,
                "current_conviction": theme.current_conviction,
                "conviction_history": []
            })

        # Run cross-reference agent
        agent = CrossReferenceAgent()
        result = agent.analyze(
            confluence_scores=confluence_data,
            time_window_days=time_window_days,
            min_sources=min_sources,
            historical_themes=historical_themes
        )

        logger.info(f"Cross-reference complete: {result.get('confluent_count', 0)} confluent themes")

        return {
            "status": "complete",
            "confluent_themes": result.get("confluent_themes", []),
            "contradictions": result.get("contradictions", []),
            "high_conviction_ideas": result.get("high_conviction_ideas", []),
            "metrics": {
                "total_themes": result.get("total_themes", 0),
                "clustered_count": result.get("clustered_themes_count", 0),
                "confluent_count": result.get("confluent_count", 0),
                "contradiction_count": result.get("contradiction_count", 0),
                "high_conviction_count": result.get("high_conviction_count", 0),
                "sources_analyzed": result.get("sources_analyzed", 0)
            },
            "analyzed_at": result.get("analyzed_at")
        }

    except ImportError as e:
        logger.error(f"Failed to import cross-reference agent: {e}")
        raise HTTPException(status_code=500, detail="Cross-reference agent not available")
    except Exception as e:
        logger.error(f"Cross-reference failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cross-reference failed: {str(e)}")


@router.get("/high-conviction")
@limiter.limit(RATE_LIMITS["default"])
async def get_high_conviction_ideas(
    request: Request,
    db: Session = Depends(get_db),
    min_conviction: float = Query(0.75, ge=0.0, le=1.0),
    min_sources: int = Query(2, ge=1, le=6),
    limit: int = Query(10, ge=1, le=50),
    user: str = Depends(verify_credentials)
):
    """
    Get high-conviction investment ideas.

    Args:
        min_conviction: Minimum conviction threshold
        min_sources: Minimum supporting sources
        limit: Maximum results

    Returns:
        List of high-conviction ideas from themes
    """
    # Query themes meeting criteria
    themes = db.query(Theme).filter(
        Theme.current_conviction >= min_conviction,
        Theme.status == 'active',
        Theme.evidence_count >= min_sources
    ).order_by(
        desc(Theme.current_conviction)
    ).limit(limit).all()

    results = []
    for theme in themes:
        # Get unique sources from evidence
        evidence_items = db.query(ThemeEvidence).filter(
            ThemeEvidence.theme_id == theme.id
        ).all()

        sources = set()
        for ev in evidence_items:
            analyzed = db.query(AnalyzedContent).filter(
                AnalyzedContent.id == ev.analyzed_content_id
            ).first()
            if analyzed:
                raw = db.query(RawContent).filter(RawContent.id == analyzed.raw_content_id).first()
                if raw:
                    src = db.query(Source).filter(Source.id == raw.source_id).first()
                    if src:
                        sources.add(src.name)

        # Calculate trend from Bayesian history
        updates = db.query(BayesianUpdate).filter(
            BayesianUpdate.theme_id == theme.id
        ).order_by(BayesianUpdate.updated_at).all()

        trend = "new"
        if len(updates) >= 2:
            first = updates[0].posterior_conviction
            last = updates[-1].posterior_conviction
            diff = last - first
            if diff > 0.1:
                trend = "rising"
            elif diff < -0.1:
                trend = "falling"
            else:
                trend = "stable"

        results.append({
            "theme": theme.name,
            "conviction": theme.current_conviction,
            "confidence_interval": [
                theme.confidence_interval_low,
                theme.confidence_interval_high
            ] if theme.confidence_interval_low else None,
            "sources": list(sources),
            "source_count": len(sources),
            "evidence_count": theme.evidence_count,
            "trend": trend,
            "first_mentioned_at": theme.first_mentioned_at.isoformat() if theme.first_mentioned_at else None,
            "status": theme.status
        })

    return {
        "high_conviction_ideas": results,
        "total": len(results),
        "filters": {
            "min_conviction": min_conviction,
            "min_sources": min_sources
        }
    }


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/stats")
@limiter.limit(RATE_LIMITS["default"])
async def get_confluence_stats(
    request: Request,
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
    user: str = Depends(verify_credentials)
):
    """
    Get confluence scoring statistics.

    Args:
        days: Time window for statistics

    Returns:
        Aggregate statistics about confluence scoring
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Total scores
    total_scores = db.query(ConfluenceScore).filter(
        ConfluenceScore.scored_at >= cutoff
    ).count()

    # Scores meeting threshold
    threshold_met = db.query(ConfluenceScore).filter(
        ConfluenceScore.scored_at >= cutoff,
        ConfluenceScore.meets_threshold == True
    ).count()

    # Average scores
    avg_result = db.query(
        func.avg(ConfluenceScore.total_score),
        func.avg(ConfluenceScore.core_total)
    ).filter(ConfluenceScore.scored_at >= cutoff).first()

    avg_total = float(avg_result[0]) if avg_result[0] else 0
    avg_core = float(avg_result[1]) if avg_result[1] else 0

    # Score distribution
    distribution = {}
    for score_val in range(15):  # 0-14
        count = db.query(ConfluenceScore).filter(
            ConfluenceScore.scored_at >= cutoff,
            ConfluenceScore.total_score == score_val
        ).count()
        if count > 0:
            distribution[str(score_val)] = count

    # Active themes
    active_themes = db.query(Theme).filter(Theme.status == 'active').count()
    high_conviction_themes = db.query(Theme).filter(
        Theme.status == 'active',
        Theme.current_conviction >= 0.75
    ).count()

    # Pillar averages
    pillar_avgs = db.query(
        func.avg(ConfluenceScore.macro_score),
        func.avg(ConfluenceScore.fundamentals_score),
        func.avg(ConfluenceScore.valuation_score),
        func.avg(ConfluenceScore.positioning_score),
        func.avg(ConfluenceScore.policy_score),
        func.avg(ConfluenceScore.price_action_score),
        func.avg(ConfluenceScore.options_vol_score)
    ).filter(ConfluenceScore.scored_at >= cutoff).first()

    return {
        "time_window_days": days,
        "total_scores": total_scores,
        "threshold_met": threshold_met,
        "threshold_rate": round(threshold_met / total_scores, 3) if total_scores > 0 else 0,
        "average_total_score": round(avg_total, 2),
        "average_core_score": round(avg_core, 2),
        "score_distribution": distribution,
        "active_themes": active_themes,
        "high_conviction_themes": high_conviction_themes,
        "pillar_averages": {
            "macro": round(float(pillar_avgs[0] or 0), 2),
            "fundamentals": round(float(pillar_avgs[1] or 0), 2),
            "valuation": round(float(pillar_avgs[2] or 0), 2),
            "positioning": round(float(pillar_avgs[3] or 0), 2),
            "policy": round(float(pillar_avgs[4] or 0), 2),
            "price_action": round(float(pillar_avgs[5] or 0), 2),
            "options_vol": round(float(pillar_avgs[6] or 0), 2)
        }
    }
