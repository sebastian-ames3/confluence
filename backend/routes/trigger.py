"""
Trigger Routes

Protected API endpoints for triggering collection and analysis.
Used by GitHub Actions scheduler and manual API calls.

Part of PRD-014: Deployment & Infrastructure Fixes.
PRD-034: Added dry_run parameter for testing collectors without database writes.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import json
import logging
import os
import asyncio

from backend.models import get_db, CollectionRun, RawContent, Source, TranscriptionStatus, SymbolState, SynthesisQualityScore
from backend.utils.deduplication import check_duplicate
from backend.utils.sanitization import sanitize_search_query
from backend.utils.data_helpers import safe_get_analysis_result, safe_get_analysis_preview

logger = logging.getLogger(__name__)

# PRD-050: Transcription queueing for trigger.py
# Import transcription functions from collect.py for video processing
try:
    from backend.routes.collect import (
        _queue_transcription_with_tracking,
        SYNC_TRANSCRIPTION
    )
    TRANSCRIPTION_AVAILABLE = True
except ImportError:
    logger.warning("Transcription functions not available - videos will not be transcribed")
    TRANSCRIPTION_AVAILABLE = False
    SYNC_TRANSCRIPTION = False
router = APIRouter()


# ============================================================================
# API Key Authentication
# ============================================================================

def verify_api_key(x_api_key: str = Header(None, alias="X-API-Key")) -> str:
    """
    Verify the API key from request header.

    Raises HTTPException 401 if key is missing or invalid.
    """
    expected_key = os.getenv("TRIGGER_API_KEY")

    if not expected_key:
        # If no key configured, allow requests (development mode)
        logger.warning("TRIGGER_API_KEY not configured - allowing unauthenticated access")
        return "development"

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide X-API-Key header."
        )

    if x_api_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return x_api_key


# ============================================================================
# Request/Response Models
# ============================================================================

class CollectRequest(BaseModel):
    """Request model for collection trigger"""
    sources: Optional[List[str]] = None  # None = all sources
    run_type: str = "manual"  # "manual", "scheduled_6am", "scheduled_6pm"
    dry_run: bool = False  # PRD-034: Skip database writes and log what would be saved


class AnalyzeRequest(BaseModel):
    """Request model for analysis trigger"""
    time_window: str = "24h"
    focus_topic: Optional[str] = None


class TriggerResponse(BaseModel):
    """Response model for trigger endpoints"""
    status: str
    job_id: int
    message: str


# ============================================================================
# Collection Trigger
# ============================================================================

@router.post("/collect")
async def trigger_collection(
    request: CollectRequest = CollectRequest(),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Trigger data collection from specified sources.

    Protected endpoint - requires X-API-Key header.
    Called by GitHub Actions scheduler or manually.

    PRD-034: Supports dry_run mode to test without database writes.

    Args:
        request: Collection request with optional source filter and dry_run flag
        db: Database session
        api_key: Validated API key

    Returns:
        Job ID and status for tracking
    """
    # Determine sources to collect from
    # NOTE: Discord and 42macro are collected locally via Task Scheduler on Sebastian's laptop
    # - Discord: Requires Discord self-bot token (local only)
    # - 42macro: Requires Chrome/Selenium (not available on Railway Nixpacks)
    # KT Technical uses requests/BeautifulSoup and can run on Railway
    all_sources = ["youtube", "substack", "kt_technical"]

    if request.sources:
        sources_to_collect = [s for s in request.sources if s in all_sources]
        if not sources_to_collect:
            raise HTTPException(
                status_code=400,
                detail=f"No valid sources specified. Available: {all_sources}"
            )
    else:
        sources_to_collect = all_sources

    # PRD-034: Log dry-run mode
    mode_str = " [DRY RUN]" if request.dry_run else ""
    logger.info(f"Collection request{mode_str} for sources: {sources_to_collect}")

    # Skip creating collection run record in dry-run mode
    if request.dry_run:
        # Run collection without creating a job record
        logger.info(f"Running dry-run collection for sources: {sources_to_collect}")
        await _run_collection_job(job_id=None, sources=sources_to_collect, dry_run=True)

        return {
            "status": "dry_run_completed",
            "job_id": None,
            "message": f"Dry-run collection completed for sources: {sources_to_collect}",
            "sources": sources_to_collect,
            "run_type": request.run_type,
            "dry_run": True
        }

    # Create collection run record
    collection_run = CollectionRun(
        run_type=request.run_type,
        started_at=datetime.utcnow(),
        status="running",
        source_results=json.dumps({}),
        errors=json.dumps([])
    )
    db.add(collection_run)
    db.commit()
    db.refresh(collection_run)

    job_id = collection_run.id
    logger.info(f"Started collection job {job_id} for sources: {sources_to_collect}")

    # Run collection synchronously - GitHub Actions waits for completion anyway
    # This ensures proper error handling and job status updates
    await _run_collection_job(job_id, sources_to_collect, dry_run=False)

    return {
        "status": "accepted",
        "job_id": job_id,
        "message": f"Collection started for sources: {sources_to_collect}",
        "sources": sources_to_collect,
        "run_type": request.run_type,
        "dry_run": False
    }


async def _run_collection_job(job_id: Optional[int], sources: List[str], dry_run: bool = False):
    """
    Execute collection job asynchronously.

    PRD-034: Supports dry_run mode.

    Args:
        job_id: CollectionRun ID (None in dry-run mode)
        sources: List of sources to collect from
        dry_run: If True, skip database writes and log what would be saved
    """
    import traceback
    from backend.models import SessionLocal

    mode_str = " [DRY RUN]" if dry_run else ""
    job_str = f"Job {job_id}" if job_id else "Dry-run"
    logger.info(f"{job_str}: Starting collection task{mode_str} for sources: {sources}")

    db = SessionLocal() if not dry_run else None
    results = {}
    errors = []
    total_items = 0
    successful = 0
    failed = 0

    try:
        for source_name in sources:
            try:
                logger.info(f"{job_str}: Collecting from {source_name}{mode_str}")
                items = await _collect_from_source(db, source_name, dry_run=dry_run)
                results[source_name] = {
                    "status": "success",
                    "items_collected": len(items),
                    "dry_run": dry_run
                }
                total_items += len(items)
                successful += 1
                action_str = "would collect" if dry_run else "collected"
                logger.info(f"{job_str}: {action_str.capitalize()} {len(items)} items from {source_name}")

            except Exception as e:
                error_msg = f"Collection from {source_name} failed: {str(e)}"
                logger.error(f"{job_str}: {error_msg}\n{traceback.format_exc()}")
                results[source_name] = {
                    "status": "failed",
                    "error": str(e)
                }
                errors.append(error_msg)
                failed += 1

        # Update collection run record (skip in dry-run mode)
        if not dry_run and job_id:
            collection_run = db.query(CollectionRun).filter(CollectionRun.id == job_id).first()
            if collection_run:
                collection_run.completed_at = datetime.utcnow()
                collection_run.status = "completed" if failed == 0 else "completed_with_errors"
                collection_run.source_results = json.dumps(results)
                collection_run.errors = json.dumps(errors)
                collection_run.total_items_collected = total_items
                collection_run.successful_sources = successful
                collection_run.failed_sources = failed
                db.commit()

        logger.info(f"{job_str}: Collection completed{mode_str}. Total: {total_items} items, {successful} successful, {failed} failed")

    except Exception as e:
        logger.error(f"{job_str}: Fatal error: {e}\n{traceback.format_exc()}")
        # Mark as failed (skip in dry-run mode)
        if not dry_run and job_id:
            try:
                collection_run = db.query(CollectionRun).filter(CollectionRun.id == job_id).first()
                if collection_run:
                    collection_run.completed_at = datetime.utcnow()
                    collection_run.status = "failed"
                    collection_run.errors = json.dumps([str(e)])
                    db.commit()
            except Exception as db_error:
                logger.error(f"{job_str}: Failed to update status: {db_error}")
    finally:
        if db:
            db.close()


async def _collect_from_source(db: Optional[Session], source_name: str, dry_run: bool = False) -> list:
    """
    Collect from a single source.

    PRD-034: Supports dry_run mode.

    Args:
        db: Database session (None in dry-run mode)
        source_name: Source to collect from
        dry_run: If True, skip database writes

    Returns:
        List of collected items
    """
    if source_name == "youtube":
        from collectors.youtube_api import YouTubeCollector

        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY not configured")

        collector = YouTubeCollector(api_key=api_key)
        items = await collector.collect()

    elif source_name == "substack":
        from collectors.substack_rss import SubstackCollector

        collector = SubstackCollector()
        items = await collector.collect()

    elif source_name == "42macro":
        from collectors.macro42_selenium import Macro42Collector

        email = os.getenv("MACRO42_EMAIL")
        password = os.getenv("MACRO42_PASSWORD")
        if not email or not password:
            raise ValueError("MACRO42_EMAIL and MACRO42_PASSWORD not configured")

        collector = Macro42Collector(email=email, password=password, headless=True)
        items = await collector.collect()

    elif source_name == "kt_technical":
        from collectors.kt_technical import KTTechnicalCollector

        email = os.getenv("KT_EMAIL")
        password = os.getenv("KT_PASSWORD")
        if not email or not password:
            raise ValueError("KT_EMAIL and KT_PASSWORD not configured")

        collector = KTTechnicalCollector(email=email, password=password)
        items = await collector.collect()

    else:
        raise ValueError(f"Unknown source: {source_name}")

    # Save items to database (skip in dry-run mode)
    if items and not dry_run:
        await _save_collected_items(db, source_name, items)
    elif items and dry_run:
        logger.info(f"[DRY RUN] Would save {len(items)} items from {source_name} to database")

    return items


async def _save_collected_items(db: Session, source_name: str, items: list) -> dict:
    """Save collected items to database with duplicate detection and transcription queueing."""
    from dateutil.parser import parse as parse_datetime

    # Get or create source
    source = db.query(Source).filter(Source.name == source_name).first()
    if not source:
        source = Source(
            name=source_name,
            type=source_name,
            active=True,
            last_collected_at=datetime.utcnow()
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    else:
        source.last_collected_at = datetime.utcnow()

    # Save each item with duplicate detection
    saved_count = 0
    skipped_duplicates = 0
    videos_to_transcribe = []  # PRD-050: Track videos for transcription

    for item in items:
        # Check for duplicates by URL or video_id
        metadata = item.get("metadata", {})
        url = item.get("url")
        video_id = metadata.get("video_id")

        if check_duplicate(db, source.id, url=url, video_id=video_id):
            skipped_duplicates += 1
            logger.debug(f"Skipping duplicate {source_name} item: {url or video_id}")
            continue

        # Parse collected_at if it's a string
        collected_at = item.get("collected_at", datetime.utcnow())
        if isinstance(collected_at, str):
            collected_at = parse_datetime(collected_at)

        raw_content = RawContent(
            source_id=source.id,
            content_type=item.get("content_type", "text"),
            content_text=item.get("content_text"),
            file_path=item.get("file_path"),
            url=item.get("url"),
            json_metadata=json.dumps(item.get("metadata", {})),
            collected_at=collected_at,
            processed=False
        )
        db.add(raw_content)
        db.flush()  # PRD-050: Get ID immediately for transcription tracking

        # PRD-050: Queue video content for transcription
        if item.get("content_type") == "video" and url:
            videos_to_transcribe.append({
                "raw_content_id": raw_content.id,
                "url": url,
                "title": metadata.get("title") or item.get("content_text", "")[:100]
            })

        saved_count += 1

    db.commit()

    if skipped_duplicates > 0:
        logger.info(f"Saved {saved_count} items, skipped {skipped_duplicates} duplicates for {source_name}")

    # PRD-050: Queue transcription for videos
    transcription_queued = 0
    if TRANSCRIPTION_AVAILABLE and videos_to_transcribe:
        transcription_mode = "sync" if SYNC_TRANSCRIPTION else "async"
        logger.info(f"Queueing {len(videos_to_transcribe)} videos for {transcription_mode} transcription from {source_name}")

        for video in videos_to_transcribe:
            try:
                await _queue_transcription_with_tracking(
                    db=db,
                    content_id=video["raw_content_id"],
                    video_url=video["url"],
                    source=source_name,
                    title=video["title"],
                    metadata=None
                )
                transcription_queued += 1
            except Exception as e:
                logger.error(f"Failed to queue transcription for {video['raw_content_id']}: {e}")

        if transcription_queued > 0:
            logger.info(f"Queued {transcription_queued} videos from {source_name} for {transcription_mode} transcription")

    return {"saved": saved_count, "skipped_duplicates": skipped_duplicates, "transcription_queued": transcription_queued}


# ============================================================================
# Analysis Trigger
# ============================================================================

@router.post("/analyze")
async def trigger_analysis(
    request: AnalyzeRequest = AnalyzeRequest(),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Trigger analysis and synthesis generation.

    Protected endpoint - requires X-API-Key header.
    Called by GitHub Actions scheduler after collection completes.

    Args:
        request: Analysis request with time window
        db: Database session
        api_key: Validated API key

    Returns:
        Job status and synthesis info
    """
    # Validate time window
    valid_windows = ["24h", "7d", "30d"]
    if request.time_window not in valid_windows:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid time_window. Use: {valid_windows}"
        )

    try:
        from agents.synthesis_agent import SynthesisAgent
        from agents.synthesis_evaluator import SynthesisEvaluatorAgent
        from agents.theme_extractor import extract_and_track_themes
        from backend.models import Synthesis, AnalyzedContent, SynthesisQualityScore

        # Get time cutoff
        time_deltas = {
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30)
        }
        cutoff = datetime.utcnow() - time_deltas[request.time_window]

        # Get analyzed content
        content_items = _get_content_for_synthesis(db, cutoff, request.focus_topic)

        if not content_items:
            return {
                "status": "no_content",
                "message": f"No analyzed content found in the past {request.time_window}",
                "content_count": 0
            }

        # Get older content for re-review recommendations
        older_cutoff = datetime.utcnow() - timedelta(days=30)
        older_content = _get_content_for_synthesis(db, older_cutoff, request.focus_topic, end_date=cutoff)

        # Get KT symbol data
        kt_symbol_data = _get_kt_symbol_data(db)

        # Generate synthesis
        agent = SynthesisAgent()
        result = agent.analyze(
            content_items=content_items,
            older_content=older_content,
            time_window=request.time_window,
            focus_topic=request.focus_topic,
            kt_symbol_data=kt_symbol_data
        )

        # Extract summary for flat columns
        exec_summary = result.get("executive_summary", {})
        synthesis_text = ""
        market_regime_str = "unclear"
        if isinstance(exec_summary, dict):
            synthesis_text = exec_summary.get("synthesis_narrative", exec_summary.get("narrative", ""))
            market_regime_str = exec_summary.get("overall_tone", "unclear")

        # Save synthesis
        synthesis = Synthesis(
            schema_version="5.0",
            synthesis=synthesis_text,
            key_themes=json.dumps([t.get("theme", "") for t in result.get("confluence_zones", [])]),
            high_conviction_ideas=json.dumps(result.get("attention_priorities", [])),
            contradictions=json.dumps(result.get("conflict_watch", [])),
            market_regime=market_regime_str,
            catalysts=json.dumps(result.get("catalyst_calendar", [])),
            synthesis_json=json.dumps(result),
            time_window=request.time_window,
            content_count=result.get("content_count", len(content_items)),
            sources_included=json.dumps(result.get("sources_included", [])),
            focus_topic=request.focus_topic,
            generated_at=datetime.utcnow()
        )
        db.add(synthesis)
        db.commit()
        db.refresh(synthesis)

        logger.info(f"Generated synthesis {synthesis.id} with {len(content_items)} content items")

        # Run quality evaluation
        if os.getenv("ENABLE_QUALITY_EVALUATION", "true").lower() == "true":
            try:
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
            except Exception as qe:
                logger.warning(f"Quality evaluation failed (non-fatal): {qe}")

        # Extract and track themes
        try:
            extract_and_track_themes(result, db)
        except Exception as te:
            logger.warning(f"Theme extraction failed (non-fatal): {te}")

        return {
            "status": "success",
            "synthesis_id": synthesis.id,
            "content_count": len(content_items),
            "time_window": request.time_window,
            "market_regime": market_regime_str,
            "key_themes": [t.get("theme", "") for t in result.get("confluence_zones", [])][:5],
            "generated_at": synthesis.generated_at.isoformat()
        }

    except ImportError as e:
        logger.error(f"Missing module for analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis module not available: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


def _get_content_for_synthesis(db: Session, cutoff: datetime, focus_topic: Optional[str] = None, end_date: Optional[datetime] = None) -> list:
    """Get analyzed content for synthesis generation."""
    from backend.models import AnalyzedContent, RawContent, Source
    from sqlalchemy import desc

    # Query analyzed content with source info
    query = db.query(AnalyzedContent, RawContent, Source).join(
        RawContent, AnalyzedContent.raw_content_id == RawContent.id
    ).join(
        Source, RawContent.source_id == Source.id
    ).filter(
        AnalyzedContent.analyzed_at >= cutoff
    )

    if end_date:
        query = query.filter(AnalyzedContent.analyzed_at < end_date)

    # Filter by topic if provided (PRD-046: sanitize for SQL injection)
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
        # PRD-047: Use safe helpers for analysis_result parsing
        analysis_data = safe_get_analysis_result(analyzed)

        # Parse metadata
        try:
            metadata = json.loads(raw.json_metadata) if raw.json_metadata else {}
        except json.JSONDecodeError:
            metadata = {}

        content_items.append({
            "id": raw.id,
            "source": source.name,
            "type": raw.content_type,
            "title": metadata.get("title", f"{source.name} content"),
            "timestamp": raw.collected_at.isoformat() if raw.collected_at else None,
            "summary": analysis_data.get("summary", safe_get_analysis_preview(analyzed, 500)),
            "themes": analyzed.key_themes.split(",") if analyzed.key_themes else [],
            "tickers": analyzed.tickers_mentioned.split(",") if analyzed.tickers_mentioned else [],
            "sentiment": analyzed.sentiment,
            "conviction": analyzed.conviction,
            "content_text": raw.content_text[:50000] if raw.content_text else "",
            "key_quotes": analysis_data.get("key_quotes", []),
        })

    return content_items


def _get_kt_symbol_data(db: Session) -> list:
    """Get KT Technical symbol data for synthesis."""
    from backend.models import SymbolState
    try:
        symbols = db.query(SymbolState).filter(
            SymbolState.kt_wave_count.isnot(None)
        ).all()
        return [
            {
                "symbol": s.symbol,
                "wave_count": s.kt_wave_count,
                "bias": s.kt_bias,
                "updated_at": s.kt_updated_at.isoformat() if s.kt_updated_at else None
            }
            for s in symbols
        ]
    except Exception as e:
        logger.warning(f"Failed to get KT symbol data: {e}")
        return []


# ============================================================================
# Job Status
# ============================================================================

@router.get("/status/{job_id}")
async def get_job_status(
    job_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Check status of a triggered collection job.

    Args:
        job_id: CollectionRun ID
        db: Database session
        api_key: Validated API key

    Returns:
        Job status and results
    """
    collection_run = db.query(CollectionRun).filter(CollectionRun.id == job_id).first()

    if not collection_run:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {
        "job_id": job_id,
        "status": collection_run.status,
        "run_type": collection_run.run_type,
        "started_at": collection_run.started_at.isoformat() if collection_run.started_at else None,
        "completed_at": collection_run.completed_at.isoformat() if collection_run.completed_at else None,
        "total_items_collected": collection_run.total_items_collected,
        "successful_sources": collection_run.successful_sources,
        "failed_sources": collection_run.failed_sources,
        "source_results": json.loads(collection_run.source_results) if collection_run.source_results else {},
        "errors": json.loads(collection_run.errors) if collection_run.errors else []
    }


@router.get("/status")
async def get_latest_jobs(
    limit: int = 5,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get status of recent collection jobs.

    Args:
        limit: Number of jobs to return
        db: Database session
        api_key: Validated API key

    Returns:
        List of recent job statuses
    """
    from sqlalchemy import desc

    runs = db.query(CollectionRun).order_by(
        desc(CollectionRun.started_at)
    ).limit(limit).all()

    return {
        "jobs": [
            {
                "job_id": run.id,
                "status": run.status,
                "run_type": run.run_type,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "total_items_collected": run.total_items_collected,
                "successful_sources": run.successful_sources,
                "failed_sources": run.failed_sources
            }
            for run in runs
        ]
    }


@router.get("/debug/chrome")
async def debug_chrome_environment(
    api_key: str = Depends(verify_api_key)
):
    """
    Debug endpoint to check Chrome/Chromium environment on Railway.

    Returns information about available Chrome binaries and environment.
    """
    import shutil
    import subprocess

    result = {
        "environment": {
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
            "HOME": os.getenv("HOME"),
            "PATH": os.getenv("PATH", "")[:500] + "...",  # Truncate long PATH
        },
        "chrome_binaries": {},
        "chromedriver": {},
        "version_checks": {}
    }

    # Check for Chrome/Chromium binaries
    for binary in ["chromium", "chromium-browser", "google-chrome", "chrome"]:
        path = shutil.which(binary)
        result["chrome_binaries"][binary] = path

    # Check for chromedriver
    chromedriver_path = shutil.which("chromedriver")
    result["chromedriver"]["path"] = chromedriver_path

    # Try to get versions
    try:
        chromium_path = result["chrome_binaries"].get("chromium") or result["chrome_binaries"].get("chromium-browser")
        if chromium_path:
            version_output = subprocess.run(
                [chromium_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            result["version_checks"]["chromium"] = version_output.stdout.strip()
    except Exception as e:
        result["version_checks"]["chromium_error"] = str(e)

    try:
        if chromedriver_path:
            version_output = subprocess.run(
                [chromedriver_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            result["version_checks"]["chromedriver"] = version_output.stdout.strip()
    except Exception as e:
        result["version_checks"]["chromedriver_error"] = str(e)

    # Check /nix/store for chromium
    try:
        nix_check = subprocess.run(
            ["find", "/nix/store", "-maxdepth", "2", "-name", "chromium*", "-type", "d"],
            capture_output=True,
            text=True,
            timeout=10
        )
        result["nix_store_chromium"] = nix_check.stdout.strip().split("\n")[:5] if nix_check.stdout else []
    except Exception as e:
        result["nix_store_chromium_error"] = str(e)

    return result


# ============================================================================
# PRD-052: Manual Transcription Processing
# ============================================================================

@router.post("/process-transcriptions")
async def process_pending_transcriptions(
    limit: int = 10,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Manually trigger processing of pending video transcriptions.

    This endpoint is useful for processing a backlog of videos that
    were collected but not transcribed (e.g., due to server restarts
    during async processing).

    The background processor runs automatically, but this endpoint
    allows manual triggering for immediate processing.

    Args:
        limit: Maximum number of pending items to process (default 10)

    Returns:
        Status of queued transcriptions
    """
    from backend.models import TranscriptionStatus, RawContent, Source
    from datetime import datetime
    from sqlalchemy import and_

    # Find pending items
    pending = db.query(TranscriptionStatus, RawContent).join(
        RawContent, TranscriptionStatus.content_id == RawContent.id
    ).filter(
        and_(
            TranscriptionStatus.status == "pending",
            TranscriptionStatus.retry_count < 3
        )
    ).order_by(TranscriptionStatus.created_at).limit(limit).all()

    if not pending:
        return {
            "status": "no_pending",
            "message": "No pending transcriptions to process",
            "processed": 0
        }

    # Get the processor and trigger processing
    queued = []
    for status, raw_content in pending:
        # Mark as processing
        status.status = "processing"
        status.last_attempt_at = datetime.utcnow()

        # Get metadata
        metadata = {}
        if raw_content.json_metadata:
            try:
                metadata = json.loads(raw_content.json_metadata)
            except json.JSONDecodeError:
                pass

        queued.append({
            "content_id": raw_content.id,
            "status_id": status.id,
            "title": metadata.get("title", "Unknown"),
            "url": raw_content.url or metadata.get("url", "Unknown")
        })

    db.commit()

    # Start processing in background
    import asyncio
    from backend.workers import get_processor
    processor = get_processor()

    # Trigger the processor to pick up items now
    asyncio.create_task(processor._process_pending())

    return {
        "status": "queued",
        "message": f"Queued {len(queued)} transcriptions for processing",
        "processed": len(queued),
        "items": queued
    }


@router.get("/transcription-status")
async def get_transcription_status(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """
    Get current transcription queue status.

    Returns counts of pending, processing, completed, and failed transcriptions.
    """
    from backend.models import TranscriptionStatus
    from sqlalchemy import func

    # Get counts by status
    counts = db.query(
        TranscriptionStatus.status,
        func.count(TranscriptionStatus.id)
    ).group_by(TranscriptionStatus.status).all()

    status_counts = {status: count for status, count in counts}

    # Get recent failures
    recent_failures = db.query(TranscriptionStatus).filter(
        TranscriptionStatus.status == "failed"
    ).order_by(TranscriptionStatus.last_attempt_at.desc()).limit(5).all()

    return {
        "summary": {
            "pending": status_counts.get("pending", 0),
            "processing": status_counts.get("processing", 0),
            "completed": status_counts.get("completed", 0),
            "failed": status_counts.get("failed", 0),
            "skipped": status_counts.get("skipped", 0)
        },
        "total": sum(status_counts.values()),
        "recent_failures": [
            {
                "id": f.id,
                "content_id": f.content_id,
                "error": f.error_message,
                "retries": f.retry_count,
                "last_attempt": f.last_attempt_at.isoformat() if f.last_attempt_at else None
            }
            for f in recent_failures
        ]
    }
