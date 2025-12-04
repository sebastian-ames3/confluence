"""
Synthesis Routes

API endpoints for research synthesis generation and retrieval.
Part of PRD-012: Dashboard Simplification.

Security (PRD-015):
- All endpoints require HTTP Basic Auth
- Rate limited to prevent abuse (especially synthesis generation)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import json
import logging

from backend.models import (
    get_db,
    Synthesis,
    CollectionRun,
    AnalyzedContent,
    RawContent,
    Source
)
from backend.utils.auth import verify_credentials
from backend.utils.rate_limiter import limiter, RATE_LIMITS

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class SynthesisGenerateRequest(BaseModel):
    """Request model for synthesis generation"""
    time_window: str = "24h"  # "24h", "7d", "30d"
    focus_topic: Optional[str] = None
    version: str = "3"  # "1" legacy, "2" actionable (PRD-020), "3" research hub (PRD-021)


class SynthesisResponse(BaseModel):
    """Response model for synthesis"""
    id: int
    synthesis: str
    key_themes: list
    high_conviction_ideas: list
    contradictions: list
    market_regime: Optional[str]
    catalysts: list
    time_window: str
    content_count: int
    sources_included: list
    focus_topic: Optional[str]
    generated_at: str


class StatusResponse(BaseModel):
    """Response model for collection status"""
    last_collection: Optional[dict]
    sources_status: list
    total_content_24h: int
    total_content_7d: int
    latest_synthesis: Optional[dict]


# ============================================================================
# Synthesis Endpoints
# ============================================================================

@router.post("/migrate-v2")
@limiter.limit(RATE_LIMITS["default"])
async def migrate_synthesis_v2(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Migrate database schema for v2 synthesis (PRD-020).
    Adds schema_version and synthesis_json columns if they don't exist.
    """
    from sqlalchemy import text

    migrations = []

    # Check and add schema_version column
    try:
        db.execute(text("SELECT schema_version FROM syntheses LIMIT 1"))
        migrations.append({"column": "schema_version", "status": "exists"})
    except Exception:
        try:
            db.execute(text("ALTER TABLE syntheses ADD COLUMN schema_version VARCHAR(10) DEFAULT '1.0'"))
            db.commit()
            migrations.append({"column": "schema_version", "status": "added"})
        except Exception as e:
            migrations.append({"column": "schema_version", "status": "error", "error": str(e)})

    # Check and add synthesis_json column
    try:
        db.execute(text("SELECT synthesis_json FROM syntheses LIMIT 1"))
        migrations.append({"column": "synthesis_json", "status": "exists"})
    except Exception:
        try:
            db.execute(text("ALTER TABLE syntheses ADD COLUMN synthesis_json TEXT"))
            db.commit()
            migrations.append({"column": "synthesis_json", "status": "added"})
        except Exception as e:
            migrations.append({"column": "synthesis_json", "status": "error", "error": str(e)})

    return {"migrations": migrations, "status": "complete"}


@router.get("/debug")
@limiter.limit(RATE_LIMITS["default"])
async def debug_synthesis(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Debug endpoint to test synthesis pipeline step by step.
    Returns diagnostic information without actually calling Claude.
    """
    import os
    import traceback

    debug_info = {
        "steps": [],
        "errors": []
    }

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

    # Step 2: Check database connection
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT 1")).fetchone()
        debug_info["steps"].append({
            "step": "db_check",
            "status": "connected"
        })
    except Exception as e:
        debug_info["errors"].append(f"db check: {str(e)}")

    # Step 3: Check analyzed content
    try:
        from sqlalchemy import or_
        cutoff = datetime.utcnow() - timedelta(days=7)
        count = db.query(AnalyzedContent).filter(
            or_(
                AnalyzedContent.analyzed_at >= cutoff,
                AnalyzedContent.analyzed_at.is_(None)
            )
        ).count()
        debug_info["steps"].append({
            "step": "content_check",
            "analyzed_content_count": count
        })
    except Exception as e:
        debug_info["errors"].append(f"content check: {str(e)}\n{traceback.format_exc()}")

    # Step 4: Try importing synthesis agent
    try:
        from agents.synthesis_agent import SynthesisAgent
        debug_info["steps"].append({
            "step": "import_agent",
            "status": "success"
        })
    except Exception as e:
        debug_info["errors"].append(f"import agent: {str(e)}\n{traceback.format_exc()}")

    # Step 5: Try creating synthesis agent
    try:
        agent = SynthesisAgent()
        debug_info["steps"].append({
            "step": "create_agent",
            "status": "success",
            "model": agent.model
        })
    except Exception as e:
        debug_info["errors"].append(f"create agent: {str(e)}\n{traceback.format_exc()}")

    # Step 6: Try a simple Claude call
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'test successful' in exactly 2 words."}]
        )
        debug_info["steps"].append({
            "step": "claude_api_call",
            "status": "success",
            "response_preview": response.content[0].text[:50] if response.content else "no content"
        })
    except Exception as e:
        debug_info["errors"].append(f"claude api call: {str(e)}\n{traceback.format_exc()}")

    return debug_info


@router.post("/generate")
@limiter.limit(RATE_LIMITS["synthesis"])
async def generate_synthesis(
    request: Request,
    synthesis_request: SynthesisGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Generate a new research synthesis.

    Triggers synthesis generation based on collected content.
    Returns immediately with job status, synthesis generated in background.
    """
    # Parse time window to timedelta
    time_deltas = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }

    if synthesis_request.time_window not in time_deltas:
        raise HTTPException(status_code=400, detail=f"Invalid time_window. Use: {list(time_deltas.keys())}")

    cutoff = datetime.utcnow() - time_deltas[synthesis_request.time_window]

    # Wrap everything in try/except to capture any errors
    import traceback
    try:
        # Get analyzed content within time window
        content_items = _get_content_for_synthesis(db, cutoff, synthesis_request.focus_topic)
        logger.info(f"Found {len(content_items)} content items for synthesis")

        if not content_items:
            return {
                "status": "no_content",
                "message": f"No analyzed content found in the past {synthesis_request.time_window}",
                "content_count": 0
            }

        # Generate synthesis
        from agents.synthesis_agent import SynthesisAgent

        logger.info(f"Creating SynthesisAgent for {len(content_items)} items...")
        agent = SynthesisAgent()

        # Determine version
        version = synthesis_request.version

        if version == "3":
            # V3: Research Consumption Hub (PRD-021)
            # Get older content for re-review recommendations (7-30 days ago)
            older_cutoff_start = datetime.utcnow() - timedelta(days=30)
            older_cutoff_end = cutoff  # End at the main cutoff (start of recent window)
            older_content = _get_content_for_synthesis(
                db, older_cutoff_start, synthesis_request.focus_topic,
                end_date=older_cutoff_end
            )
            logger.info(f"Found {len(older_content)} older items for re-review scanning")

            logger.info("Calling agent.analyze_v3() for research consumption synthesis...")
            result = agent.analyze_v3(
                content_items=content_items,
                older_content=older_content,
                time_window=synthesis_request.time_window,
                focus_topic=synthesis_request.focus_topic
            )
            logger.info(f"V3 Analysis complete: {len(result.get('confluence_zones', []))} confluence zones, "
                       f"{len(result.get('attention_priorities', []))} priorities")

        elif version == "2":
            logger.info("Calling agent.analyze_v2() for actionable synthesis...")
            result = agent.analyze_v2(
                content_items=content_items,
                time_window=synthesis_request.time_window,
                focus_topic=synthesis_request.focus_topic
            )
            logger.info(f"V2 Analysis complete: {len(result.get('tactical_ideas', []))} tactical, "
                       f"{len(result.get('strategic_ideas', []))} strategic ideas")
        else:
            logger.info("Calling agent.analyze() for legacy synthesis...")
            result = agent.analyze(
                content_items=content_items,
                time_window=synthesis_request.time_window,
                focus_topic=synthesis_request.focus_topic
            )
            logger.info(f"V1 Analysis complete, got result with keys: {list(result.keys())}")

        # Extract synthesis text based on version
        if version == "3":
            # V3: executive_summary.narrative
            exec_summary = result.get("executive_summary", {})
            synthesis_text = exec_summary.get("narrative", "") if isinstance(exec_summary, dict) else ""
            market_regime_str = exec_summary.get("overall_tone", "unclear") if isinstance(exec_summary, dict) else "unclear"
        else:
            # V2/V1: synthesis_summary or synthesis
            synthesis_text = result.get("synthesis_summary") or result.get("synthesis", "")
            # Extract market regime (v2 is object, v1 is string)
            market_regime = result.get("market_regime")
            if isinstance(market_regime, dict):
                market_regime_str = market_regime.get("current", "unclear")
            else:
                market_regime_str = market_regime

        # Determine schema version
        if version == "3":
            schema_ver = "3.0"
        elif version == "2":
            schema_ver = "2.0"
        else:
            schema_ver = "1.0"

        # Save to database
        synthesis = Synthesis(
            schema_version=schema_ver,
            synthesis=synthesis_text,
            key_themes=json.dumps(result.get("key_themes", []) or [t.get("theme", "") for t in result.get("confluence_zones", [])]),
            high_conviction_ideas=json.dumps(result.get("high_conviction_ideas", []) or result.get("tactical_ideas", []) or result.get("attention_priorities", [])),
            contradictions=json.dumps(result.get("contradictions", []) or result.get("watch_list", []) or result.get("conflict_watch", [])),
            market_regime=market_regime_str,
            catalysts=json.dumps(result.get("catalysts", []) or result.get("catalyst_calendar", [])),
            synthesis_json=json.dumps(result) if version in ["2", "3"] else None,
            time_window=synthesis_request.time_window,
            content_count=result.get("content_count", len(content_items)),
            sources_included=json.dumps(result.get("sources_included", [])),
            focus_topic=synthesis_request.focus_topic,
            generated_at=datetime.utcnow()
        )
        db.add(synthesis)
        db.commit()
        db.refresh(synthesis)

        # Return appropriate response format
        if version == "3":
            return {
                "status": "success",
                "version": "3.0",
                "synthesis_id": synthesis.id,
                **result,
                "generated_at": synthesis.generated_at.isoformat()
            }
        elif version == "2":
            return {
                "status": "success",
                "version": "2.0",
                "synthesis_id": synthesis.id,
                **result,
                "generated_at": synthesis.generated_at.isoformat()
            }
        else:
            return {
                "status": "success",
                "version": "1.0",
                "synthesis_id": synthesis.id,
                "synthesis": result.get("synthesis"),
                "key_themes": result.get("key_themes", []),
                "high_conviction_ideas": result.get("high_conviction_ideas", []),
                "content_count": result.get("content_count", len(content_items)),
                "generated_at": synthesis.generated_at.isoformat()
            }

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
    user: str = Depends(verify_credentials)
):
    """
    Get the most recent synthesis.

    Optionally filter by time_window (24h, 7d, 30d).
    """
    query = db.query(Synthesis)

    if time_window:
        query = query.filter(Synthesis.time_window == time_window)

    synthesis = query.order_by(desc(Synthesis.generated_at)).first()

    if not synthesis:
        return {
            "status": "not_found",
            "message": "No synthesis found. Generate one first."
        }

    # Check if this is a v2/v3 synthesis with full JSON
    schema_version = getattr(synthesis, 'schema_version', '1.0') or '1.0'
    synthesis_json = getattr(synthesis, 'synthesis_json', None)

    if schema_version in ["2.0", "3.0"] and synthesis_json:
        # Return full v2/v3 response
        try:
            data = json.loads(synthesis_json)
            data["id"] = synthesis.id
            data["version"] = schema_version
            return data
        except json.JSONDecodeError:
            pass  # Fall back to v1 format

    # Return v1 format (backwards compatibility)
    return {
        "id": synthesis.id,
        "version": schema_version,
        "synthesis": synthesis.synthesis,
        "key_themes": json.loads(synthesis.key_themes) if synthesis.key_themes else [],
        "high_conviction_ideas": json.loads(synthesis.high_conviction_ideas) if synthesis.high_conviction_ideas else [],
        "contradictions": json.loads(synthesis.contradictions) if synthesis.contradictions else [],
        "market_regime": synthesis.market_regime,
        "catalysts": json.loads(synthesis.catalysts) if synthesis.catalysts else [],
        "time_window": synthesis.time_window,
        "content_count": synthesis.content_count,
        "sources_included": json.loads(synthesis.sources_included) if synthesis.sources_included else [],
        "focus_topic": synthesis.focus_topic,
        "generated_at": synthesis.generated_at.isoformat() if synthesis.generated_at else None
    }


@router.get("/history")
@limiter.limit(RATE_LIMITS["default"])
async def get_synthesis_history(
    request: Request,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Get synthesis history.

    Returns a list of past syntheses ordered by generation time.
    """
    syntheses = db.query(Synthesis).order_by(
        desc(Synthesis.generated_at)
    ).offset(offset).limit(limit).all()

    total = db.query(func.count(Synthesis.id)).scalar()

    return {
        "syntheses": [
            {
                "id": s.id,
                "synthesis_preview": s.synthesis[:200] + "..." if len(s.synthesis) > 200 else s.synthesis,
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


@router.get("/{synthesis_id}")
@limiter.limit(RATE_LIMITS["default"])
async def get_synthesis_by_id(
    request: Request,
    synthesis_id: int,
    db: Session = Depends(get_db),
    user: str = Depends(verify_credentials)
):
    """
    Get a specific synthesis by ID.
    """
    synthesis = db.query(Synthesis).filter(Synthesis.id == synthesis_id).first()

    if not synthesis:
        raise HTTPException(status_code=404, detail="Synthesis not found")

    return {
        "id": synthesis.id,
        "synthesis": synthesis.synthesis,
        "key_themes": json.loads(synthesis.key_themes) if synthesis.key_themes else [],
        "high_conviction_ideas": json.loads(synthesis.high_conviction_ideas) if synthesis.high_conviction_ideas else [],
        "contradictions": json.loads(synthesis.contradictions) if synthesis.contradictions else [],
        "market_regime": synthesis.market_regime,
        "catalysts": json.loads(synthesis.catalysts) if synthesis.catalysts else [],
        "time_window": synthesis.time_window,
        "content_count": synthesis.content_count,
        "sources_included": json.loads(synthesis.sources_included) if synthesis.sources_included else [],
        "focus_topic": synthesis.focus_topic,
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
    user: str = Depends(verify_credentials)
):
    """
    Get collection status overview for dashboard.

    Returns:
    - Last collection run info
    - Per-source status
    - Content counts
    - Latest synthesis info
    """
    # Get last collection run
    last_run = db.query(CollectionRun).order_by(
        desc(CollectionRun.started_at)
    ).first()

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

    # Get per-source status
    sources = db.query(Source).filter(Source.active == True).all()
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    sources_status = []
    for source in sources:
        # Count content in last 24h
        count_24h = db.query(func.count(RawContent.id)).filter(
            RawContent.source_id == source.id,
            RawContent.collected_at >= twenty_four_hours_ago
        ).scalar()

        # Count content in last 7d
        count_7d = db.query(func.count(RawContent.id)).filter(
            RawContent.source_id == source.id,
            RawContent.collected_at >= seven_days_ago
        ).scalar()

        sources_status.append({
            "name": source.name,
            "type": source.type,
            "last_collected": source.last_collected_at.isoformat() if source.last_collected_at else None,
            "items_24h": count_24h,
            "items_7d": count_7d
        })

    # Get total content counts
    total_24h = db.query(func.count(RawContent.id)).filter(
        RawContent.collected_at >= twenty_four_hours_ago
    ).scalar()

    total_7d = db.query(func.count(RawContent.id)).filter(
        RawContent.collected_at >= seven_days_ago
    ).scalar()

    # Get latest synthesis
    latest_synthesis = db.query(Synthesis).order_by(
        desc(Synthesis.generated_at)
    ).first()

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
    user: str = Depends(verify_credentials)
):
    """
    Get recent collection runs.
    """
    runs = db.query(CollectionRun).order_by(
        desc(CollectionRun.started_at)
    ).limit(limit).all()

    return {
        "collection_runs": [
            {
                "id": run.id,
                "run_type": run.run_type,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "status": run.status,
                "total_items": run.total_items_collected,
                "successful_sources": run.successful_sources,
                "failed_sources": run.failed_sources,
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
        end_date: Optional end date (content must be before this) - for older content queries

    Returns list of dicts with content info for the synthesis agent.
    """
    # Query analyzed content with source info
    # Include items with NULL analyzed_at (for backwards compatibility)
    from sqlalchemy import or_, and_
    query = db.query(AnalyzedContent, RawContent, Source).join(
        RawContent, AnalyzedContent.raw_content_id == RawContent.id
    ).join(
        Source, RawContent.source_id == Source.id
    )

    # Apply date filters
    if end_date:
        # For older content: between cutoff and end_date
        query = query.filter(
            and_(
                or_(
                    AnalyzedContent.analyzed_at >= cutoff,
                    AnalyzedContent.analyzed_at.is_(None)
                ),
                or_(
                    AnalyzedContent.analyzed_at < end_date,
                    AnalyzedContent.analyzed_at.is_(None)
                )
            )
        )
    else:
        # For recent content: after cutoff
        query = query.filter(
            or_(
                AnalyzedContent.analyzed_at >= cutoff,
                AnalyzedContent.analyzed_at.is_(None)
            )
        )

    # Filter by topic if provided
    if focus_topic:
        topic_lower = focus_topic.lower()
        query = query.filter(
            (AnalyzedContent.key_themes.ilike(f"%{topic_lower}%")) |
            (AnalyzedContent.tickers_mentioned.ilike(f"%{topic_lower}%"))
        )

    results = query.order_by(desc(AnalyzedContent.analyzed_at)).all()

    content_items = []
    for analyzed, raw, source in results:
        # Parse analysis result
        try:
            analysis_data = json.loads(analyzed.analysis_result) if analyzed.analysis_result else {}
        except json.JSONDecodeError:
            analysis_data = {}

        # Parse metadata
        try:
            metadata = json.loads(raw.json_metadata) if raw.json_metadata else {}
        except json.JSONDecodeError:
            metadata = {}

        content_items.append({
            "source": source.name,
            "type": raw.content_type,
            "title": metadata.get("title", f"{source.name} content"),
            "timestamp": raw.collected_at.isoformat() if raw.collected_at else None,
            "summary": analysis_data.get("summary", analyzed.analysis_result[:500] if analyzed.analysis_result else ""),
            "themes": analyzed.key_themes.split(",") if analyzed.key_themes else [],
            "tickers": analyzed.tickers_mentioned.split(",") if analyzed.tickers_mentioned else [],
            "sentiment": analyzed.sentiment,
            "conviction": analyzed.conviction,
            "content_text": raw.content_text[:1000] if raw.content_text else ""
        })

    return content_items
