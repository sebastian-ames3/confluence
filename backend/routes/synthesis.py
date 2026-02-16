"""
Synthesis Routes

API endpoints for research synthesis generation and retrieval.
Single pipeline — one generation method, one output schema, no versions or tiers.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json
import logging
import os

from backend.models import (
    get_db,
    Synthesis,
    CollectionRun,
    AnalyzedContent,
    RawContent,
    Source,
    SynthesisQualityScore,
    SymbolState,
    ConfluenceScore
)
from backend.utils.auth import verify_jwt_or_basic
from backend.utils.rate_limiter import limiter, RATE_LIMITS
from backend.utils.sanitization import sanitize_search_query
from backend.utils.data_helpers import safe_get_analysis_result, safe_get_analysis_preview
from agents.theme_extractor import extract_and_track_themes
from agents.synthesis_evaluator import SynthesisEvaluatorAgent

logger = logging.getLogger(__name__)
router = APIRouter()

# Synthesis generation timeout (default 600s for per-source + merge pipeline)
SYNTHESIS_TIMEOUT_SECONDS = int(os.getenv("SYNTHESIS_TIMEOUT", "600"))
synthesis_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="synthesis_")

# YouTube channel display names (maps collector keys to human-readable names)
YOUTUBE_CHANNEL_DISPLAY = {
    "peter_diamandis": "Moonshots",
    "jordi_visser": "Jordi Visser Labs",
    "forward_guidance": "Forward Guidance",
    "42macro": "42 Macro"
}


class SynthesisGenerateRequest(BaseModel):
    """Request model for synthesis generation."""
    time_window: str = "24h"  # "24h", "7d", "30d"
    focus_topic: Optional[str] = None


# ============================================================================
# Synthesis Endpoints
# ============================================================================

@router.post("/generate")
@limiter.limit(RATE_LIMITS["synthesis"])
async def generate_synthesis(
    request: Request,
    synthesis_request: SynthesisGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """
    Generate a new research synthesis.

    Single pipeline: main synthesis + per-source breakdowns + content summaries.
    """
    time_deltas = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }

    if synthesis_request.time_window not in time_deltas:
        raise HTTPException(status_code=400, detail=f"Invalid time_window. Use: {list(time_deltas.keys())}")

    cutoff = datetime.utcnow() - time_deltas[synthesis_request.time_window]

    import traceback
    try:
        # Get recent content
        content_items = _get_content_for_synthesis(db, cutoff, synthesis_request.focus_topic)
        logger.info(f"Found {len(content_items)} content items for synthesis")

        if not content_items:
            return {
                "status": "no_content",
                "message": f"No analyzed content found in the past {synthesis_request.time_window}",
                "content_count": 0
            }

        # Get older content for re-review recommendations (7-30 days ago)
        older_cutoff_start = datetime.utcnow() - timedelta(days=30)
        older_content = _get_content_for_synthesis(
            db, older_cutoff_start, synthesis_request.focus_topic,
            end_date=cutoff
        )
        logger.info(f"Found {len(older_content)} older items for re-review scanning")

        # Get KT Technical symbol data
        kt_symbol_data = _get_kt_symbol_data(db)

        # Get 7-pillar confluence scores for the time window
        pillar_scores = _get_pillar_scores_for_synthesis(db, cutoff)
        if pillar_scores:
            logger.info(f"Including pillar scores from {len(pillar_scores)} sources in synthesis")

        # Generate synthesis
        from agents.synthesis_agent import SynthesisAgent
        agent = SynthesisAgent()

        async def run_synthesis_with_timeout(synthesis_func, *args, **kwargs):
            """Run synthesis with timeout protection."""
            loop = asyncio.get_event_loop()
            try:
                return await asyncio.wait_for(
                    loop.run_in_executor(
                        synthesis_executor,
                        lambda: synthesis_func(*args, **kwargs)
                    ),
                    timeout=SYNTHESIS_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                logger.error(f"Synthesis generation timed out after {SYNTHESIS_TIMEOUT_SECONDS}s")
                raise HTTPException(
                    status_code=504,
                    detail={
                        "error": "synthesis_timeout",
                        "message": f"Synthesis generation timed out after {SYNTHESIS_TIMEOUT_SECONDS} seconds.",
                        "timeout_seconds": SYNTHESIS_TIMEOUT_SECONDS
                    }
                )

        logger.info(f"Generating synthesis for {len(content_items)} items...")
        result = await run_synthesis_with_timeout(
            agent.analyze,
            content_items=content_items,
            older_content=older_content,
            time_window=synthesis_request.time_window,
            focus_topic=synthesis_request.focus_topic,
            kt_symbol_data=kt_symbol_data,
            pillar_scores=pillar_scores if pillar_scores else None
        )
        logger.info(
            f"Synthesis complete: {len(result.get('source_breakdowns', {}))} source breakdowns, "
            f"{len(result.get('content_summaries', []))} content summaries"
        )

        # Extract summary text for the flat synthesis column (used by /history previews)
        exec_summary = result.get("executive_summary", {})
        synthesis_text = ""
        market_regime_str = "unclear"
        if isinstance(exec_summary, dict):
            synthesis_text = exec_summary.get("synthesis_narrative", exec_summary.get("narrative", ""))
            market_regime_str = exec_summary.get("overall_tone", "unclear")

        # Save to database
        synthesis = Synthesis(
            schema_version="5.0",
            synthesis=synthesis_text,
            key_themes=json.dumps([t.get("theme", "") for t in result.get("confluence_zones", [])]),
            high_conviction_ideas=json.dumps(result.get("attention_priorities", [])),
            contradictions=json.dumps(result.get("conflict_watch", [])),
            market_regime=market_regime_str,
            catalysts=json.dumps(result.get("catalyst_calendar", [])),
            synthesis_json=json.dumps(result),
            time_window=synthesis_request.time_window,
            content_count=result.get("content_count", len(content_items)),
            sources_included=json.dumps(result.get("sources_included", [])),
            focus_topic=synthesis_request.focus_topic,
            generated_at=datetime.utcnow()
        )
        db.add(synthesis)
        db.commit()
        db.refresh(synthesis)

        # Run quality evaluation
        quality_evaluation = None
        if os.getenv("ENABLE_QUALITY_EVALUATION", "true").lower() == "true":
            try:
                logger.info(f"Running quality evaluation for synthesis {synthesis.id}...")
                evaluator = SynthesisEvaluatorAgent()
                quality_result = evaluator.evaluate(
                    synthesis_output=result,
                    original_content=content_items
                )

                quality_score = SynthesisQualityScore(
                    synthesis_id=synthesis.id,
                    quality_score=quality_result["quality_score"],
                    grade=quality_result["grade"],
                    confluence_detection=quality_result["confluence_detection"],
                    evidence_preservation=quality_result["evidence_preservation"],
                    source_attribution=quality_result["source_attribution"],
                    youtube_channel_granularity=quality_result["youtube_channel_granularity"],
                    nuance_retention=quality_result["nuance_retention"],
                    actionability=quality_result["actionability"],
                    theme_continuity=quality_result["theme_continuity"],
                    flags=json.dumps(quality_result.get("flags", [])),
                    prompt_suggestions=json.dumps(quality_result.get("prompt_suggestions", []))
                )
                db.add(quality_score)
                db.commit()

                quality_evaluation = quality_result
                logger.info(f"Quality evaluation complete: {quality_result['grade']} ({quality_result['quality_score']}/100)")
            except Exception as quality_error:
                logger.warning(f"Quality evaluation failed (non-fatal): {str(quality_error)}")

        # Extract and track themes
        try:
            theme_result = extract_and_track_themes(result, db)
            logger.info(f"Theme extraction complete: {theme_result.get('created', 0)} created, "
                       f"{theme_result.get('updated', 0)} updated")
        except Exception as theme_error:
            db.rollback()
            logger.warning(f"Theme extraction failed (non-fatal): {str(theme_error)}")

        # Return response
        response = {
            "status": "success",
            "synthesis_id": synthesis.id,
            **result,
            "generated_at": synthesis.generated_at.isoformat()
        }
        if quality_evaluation:
            response["quality_evaluation"] = quality_evaluation
        return response

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Synthesis generation failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.get("/latest")
@limiter.limit(RATE_LIMITS["default"])
async def get_latest_synthesis(
    request: Request,
    time_window: Optional[str] = Query(None, description="Filter by time window"),
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """Get the most recent synthesis."""
    query = db.query(Synthesis)

    if time_window:
        query = query.filter(Synthesis.time_window == time_window)

    synthesis = query.order_by(desc(Synthesis.generated_at)).first()

    if not synthesis:
        return {
            "status": "not_found",
            "message": "No synthesis found. Generate one first."
        }

    # Read from synthesis_json (the full structured output)
    synthesis_json = getattr(synthesis, 'synthesis_json', None)

    if synthesis_json:
        try:
            data = json.loads(synthesis_json)
            data["id"] = synthesis.id
            return data
        except json.JSONDecodeError:
            pass

    # Fallback for very old records without synthesis_json
    return {
        "status": "not_found",
        "message": "No synthesis in current format. Generate a new one."
    }


@router.get("/history")
@limiter.limit(RATE_LIMITS["default"])
async def get_synthesis_history(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """Get synthesis history."""
    syntheses = db.query(Synthesis).order_by(
        desc(Synthesis.generated_at)
    ).offset(offset).limit(limit).all()

    total = db.query(func.count(Synthesis.id)).scalar()

    return {
        "syntheses": [
            {
                "id": s.id,
                "synthesis_preview": (s.synthesis[:200] + "...") if s.synthesis and len(s.synthesis) > 200 else (s.synthesis or ""),
                "key_themes": json.loads(s.key_themes) if s.key_themes else [],
                "time_window": s.time_window,
                "content_count": s.content_count,
                "market_regime": s.market_regime,
                "generated_at": s.generated_at.isoformat() if s.generated_at else None
            }
            for s in syntheses
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/debug")
@limiter.limit(RATE_LIMITS["default"])
async def debug_synthesis(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """Debug endpoint to test synthesis pipeline step by step."""
    import traceback

    debug_info = {"steps": [], "errors": []}

    # Step 1: Check environment
    try:
        claude_key = os.getenv("CLAUDE_API_KEY")
        debug_info["steps"].append({
            "step": "check_env",
            "claude_api_key_exists": bool(claude_key),
            "claude_api_key_prefix": claude_key[:10] + "..." if claude_key else None
        })
    except Exception as e:
        debug_info["errors"].append(f"env check: {str(e)}")

    # Step 2: Check database
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1")).fetchone()
        debug_info["steps"].append({"step": "db_check", "status": "connected"})
    except Exception as e:
        debug_info["errors"].append(f"db check: {str(e)}")

    # Step 3: Check content
    try:
        cutoff = datetime.utcnow() - timedelta(days=7)
        count = db.query(AnalyzedContent).filter(
            AnalyzedContent.analyzed_at >= cutoff
        ).count()
        debug_info["steps"].append({"step": "content_check", "analyzed_content_count": count})
    except Exception as e:
        debug_info["errors"].append(f"content check: {str(e)}\n{traceback.format_exc()}")

    # Step 4: Import agent
    try:
        from agents.synthesis_agent import SynthesisAgent
        debug_info["steps"].append({"step": "import_agent", "status": "success"})
    except Exception as e:
        debug_info["errors"].append(f"import agent: {str(e)}\n{traceback.format_exc()}")

    # Step 5: Create agent
    try:
        agent = SynthesisAgent()
        debug_info["steps"].append({"step": "create_agent", "status": "success", "model": agent.model})
    except Exception as e:
        debug_info["errors"].append(f"create agent: {str(e)}\n{traceback.format_exc()}")

    # Step 6: Test Claude API
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        response = client.messages.create(
            model=os.getenv("ANALYSIS_MODEL", "claude-sonnet-4-20250514"),
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'test successful' in exactly 2 words."}]
        )
        debug_info["steps"].append({
            "step": "claude_api_call", "status": "success",
            "response_preview": response.content[0].text[:50] if response.content else "no content"
        })
    except Exception as e:
        debug_info["errors"].append(f"claude api call: {str(e)}\n{traceback.format_exc()}")

    return debug_info


@router.get("/{synthesis_id}")
@limiter.limit(RATE_LIMITS["default"])
async def get_synthesis_by_id(
    request: Request,
    synthesis_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """Get a specific synthesis by ID."""
    synthesis = db.query(Synthesis).filter(Synthesis.id == synthesis_id).first()

    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis not found")

    # Try full JSON first
    synthesis_json = getattr(synthesis, 'synthesis_json', None)
    if synthesis_json:
        try:
            data = json.loads(synthesis_json)
            data["id"] = synthesis.id
            return data
        except json.JSONDecodeError:
            pass

    # Fallback for old records
    return {
        "id": synthesis.id,
        "synthesis": synthesis.synthesis or "",
        "key_themes": json.loads(synthesis.key_themes) if synthesis.key_themes else [],
        "market_regime": synthesis.market_regime or "unknown",
        "time_window": synthesis.time_window,
        "content_count": synthesis.content_count,
        "generated_at": synthesis.generated_at.isoformat() if synthesis.generated_at else None
    }


# ============================================================================
# Status Endpoints
# ============================================================================

@router.get("/status/overview")
@limiter.limit(RATE_LIMITS["default"])
async def get_status_overview(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """Get collection status overview for dashboard."""
    last_run = db.query(CollectionRun).order_by(desc(CollectionRun.started_at)).first()

    last_collection = None
    if last_run:
        last_collection = {
            "id": last_run.id,
            "run_type": last_run.run_type,
            "started_at": last_run.started_at.isoformat() if last_run.started_at else None,
            "completed_at": last_run.completed_at.isoformat() if last_run.completed_at else None,
            "status": last_run.status,
            "total_items": last_run.total_items_collected,
            "successful_sources": last_run.successful_sources,
            "failed_sources": last_run.failed_sources
        }

    sources = db.query(Source).filter(Source.active == True).all()
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    sources_status = []
    for source in sources:
        count_24h = db.query(func.count(RawContent.id)).filter(
            RawContent.source_id == source.id, RawContent.collected_at >= twenty_four_hours_ago
        ).scalar()
        count_7d = db.query(func.count(RawContent.id)).filter(
            RawContent.source_id == source.id, RawContent.collected_at >= seven_days_ago
        ).scalar()
        sources_status.append({
            "name": source.name, "type": source.type,
            "last_collected": source.last_collected_at.isoformat() if source.last_collected_at else None,
            "items_24h": count_24h, "items_7d": count_7d
        })

    total_24h = db.query(func.count(RawContent.id)).filter(RawContent.collected_at >= twenty_four_hours_ago).scalar()
    total_7d = db.query(func.count(RawContent.id)).filter(RawContent.collected_at >= seven_days_ago).scalar()

    latest_synthesis = db.query(Synthesis).order_by(desc(Synthesis.generated_at)).first()
    synthesis_info = None
    if latest_synthesis:
        synthesis_info = {
            "id": latest_synthesis.id,
            "time_window": latest_synthesis.time_window,
            "content_count": latest_synthesis.content_count,
            "market_regime": latest_synthesis.market_regime,
            "generated_at": latest_synthesis.generated_at.isoformat() if latest_synthesis.generated_at else None,
            "key_themes": json.loads(latest_synthesis.key_themes) if latest_synthesis.key_themes else []
        }

    return {
        "last_collection": last_collection,
        "sources_status": sources_status,
        "total_content_24h": total_24h,
        "total_content_7d": total_7d,
        "latest_synthesis": synthesis_info
    }


@router.get("/status/collections")
@limiter.limit(RATE_LIMITS["default"])
async def get_collection_history(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: str = Depends(verify_jwt_or_basic)
):
    """Get recent collection runs."""
    runs = db.query(CollectionRun).order_by(desc(CollectionRun.started_at)).limit(limit).all()

    return {
        "collection_runs": [
            {
                "id": run.id, "run_type": run.run_type,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "status": run.status, "total_items": run.total_items_collected,
                "successful_sources": run.successful_sources, "failed_sources": run.failed_sources,
                "source_results": json.loads(run.source_results) if run.source_results else {},
                "errors": json.loads(run.errors) if run.errors else []
            }
            for run in runs
        ]
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _get_content_for_synthesis(
    db: Session,
    cutoff: datetime,
    focus_topic: Optional[str] = None,
    end_date: Optional[datetime] = None
) -> list:
    """
    Get analyzed content for synthesis generation.

    Args:
        db: Database session
        cutoff: Start date (content must be after this)
        focus_topic: Optional topic filter
        end_date: Optional end date (for older content queries)

    Returns list of dicts with content info for the synthesis agent.
    """
    from sqlalchemy import and_
    query = db.query(AnalyzedContent, RawContent, Source).join(
        RawContent, AnalyzedContent.raw_content_id == RawContent.id
    ).join(
        Source, RawContent.source_id == Source.id
    )

    if end_date:
        query = query.filter(
            and_(
                AnalyzedContent.analyzed_at >= cutoff,
                AnalyzedContent.analyzed_at < end_date
            )
        )
    else:
        query = query.filter(AnalyzedContent.analyzed_at >= cutoff)

    if focus_topic:
        safe_topic = sanitize_search_query(focus_topic.lower())
        if safe_topic:
            query = query.filter(
                (AnalyzedContent.key_themes.ilike(f"%{safe_topic}%")) |
                (AnalyzedContent.tickers_mentioned.ilike(f"%{safe_topic}%"))
            )

    results = query.order_by(desc(AnalyzedContent.analyzed_at)).all()

    content_items = []
    for analyzed, raw, source in results:
        analysis_data = safe_get_analysis_result(analyzed)

        try:
            metadata = json.loads(raw.json_metadata) if raw.json_metadata else {}
        except json.JSONDecodeError:
            metadata = {}

        channel_name = None
        channel_display = None
        if source.name == "youtube":
            channel_name = metadata.get("channel_name")
            if channel_name:
                channel_display = YOUTUBE_CHANNEL_DISPLAY.get(channel_name, channel_name.replace("_", " ").title())
            else:
                channel_display = "Youtube"

        content_items.append({
            "id": raw.id,
            "source": source.name,
            "channel": channel_name,
            "channel_display": channel_display,
            "type": raw.content_type,
            "title": metadata.get("title", f"{source.name} content"),
            "timestamp": raw.collected_at.isoformat() if raw.collected_at else None,
            "summary": analysis_data.get("summary", safe_get_analysis_preview(analyzed, 500)),
            "themes": analyzed.key_themes.split(",") if analyzed.key_themes else [],
            "tickers": analyzed.tickers_mentioned.split(",") if analyzed.tickers_mentioned else [],
            "sentiment": analyzed.sentiment,
            "conviction": analyzed.conviction,
            "content_text": raw.content_text or "",
            "key_quotes": analysis_data.get("key_quotes", []),
        })

    return content_items


def _get_kt_symbol_data(db: Session) -> list:
    """Get KT Technical symbol-level data from SymbolState."""
    states = db.query(SymbolState).filter(SymbolState.kt_last_updated.isnot(None)).all()

    kt_data = []
    for state in states:
        kt_data.append({
            "symbol": state.symbol,
            "wave_position": state.kt_wave_position,
            "wave_direction": state.kt_wave_direction,
            "wave_phase": state.kt_wave_phase,
            "bias": state.kt_bias,
            "primary_target": state.kt_primary_target,
            "primary_support": state.kt_primary_support,
            "invalidation": state.kt_invalidation,
            "notes": state.kt_notes,
            "last_updated": state.kt_last_updated.isoformat() if state.kt_last_updated else None
        })

    logger.info(f"Found KT Technical data for {len(kt_data)} symbols")
    return kt_data


def _get_pillar_scores_for_synthesis(db: Session, cutoff: datetime) -> dict:
    """
    Get 7-pillar confluence scores for content in the time window, grouped by source.

    Returns dict keyed by source name with pillar score summaries.
    """
    results = db.query(ConfluenceScore, AnalyzedContent, RawContent, Source).join(
        AnalyzedContent, ConfluenceScore.analyzed_content_id == AnalyzedContent.id
    ).join(
        RawContent, AnalyzedContent.raw_content_id == RawContent.id
    ).join(
        Source, RawContent.source_id == Source.id
    ).filter(
        ConfluenceScore.scored_at >= cutoff
    ).all()

    if not results:
        return {}

    by_source = {}
    for score, analyzed, raw, source in results:
        source_name = source.name
        if source_name not in by_source:
            by_source[source_name] = []

        by_source[source_name].append({
            "pillar_scores": {
                "macro": score.macro_score,
                "fundamentals": score.fundamentals_score,
                "valuation": score.valuation_score,
                "positioning": score.positioning_score,
                "policy": score.policy_score,
                "price_action": score.price_action_score,
                "options_vol": score.options_vol_score,
            },
            "core_total": score.core_total,
            "total_score": score.total_score,
            "meets_threshold": score.meets_threshold,
        })

    # Build compact summary per source
    summary = {}
    for source_name, scores in by_source.items():
        avg_core = sum(s["core_total"] for s in scores) / len(scores)
        avg_total = sum(s["total_score"] for s in scores) / len(scores)
        threshold_met_count = sum(1 for s in scores if s["meets_threshold"])
        summary[source_name] = {
            "score_count": len(scores),
            "avg_core_total": round(avg_core, 1),
            "avg_total_score": round(avg_total, 1),
            "threshold_met": threshold_met_count,
            "scores": scores,
        }

    logger.info(f"Found pillar scores for {len(summary)} sources ({sum(len(v['scores']) for v in summary.values())} total)")
    return summary
