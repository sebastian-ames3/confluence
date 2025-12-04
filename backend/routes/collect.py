"""
Collection Routes

API endpoints for triggering data collection from research sources.
Includes endpoints for receiving data from local laptop scripts:
- Discord: dev/scripts/discord_local.py
- 42macro: dev/scripts/macro42_local.py

PRD-018: Added video transcription integration with TranscriptHarvesterAgent.
Videos from Discord and 42macro are automatically transcribed after collection.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import json
import os
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from backend.models import get_db, RawContent, Source, SessionLocal
from backend.utils.deduplication import check_duplicate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collect", tags=["collect"])

# Thread pool for async video transcription (PRD-018)
# Limited to 2 workers to avoid overwhelming the system
transcription_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="transcribe_")


def _transcribe_video_sync(
    raw_content_id: int,
    video_url: str,
    source: str,
    title: Optional[str] = None
) -> bool:
    """
    Transcribe a video and update the database record.

    This runs synchronously in a thread pool worker.
    PRD-018: Video transcription for all sources.

    Args:
        raw_content_id: ID of the RawContent record to update
        video_url: URL of the video to transcribe
        source: Source name (discord, 42macro, youtube)
        title: Optional title for metadata

    Returns:
        True if transcription succeeded, False otherwise
    """
    db = None
    try:
        from agents.transcript_harvester import TranscriptHarvesterAgent

        logger.info(f"Starting transcription for raw_content_id={raw_content_id}, url={video_url[:50]}...")

        # Initialize the harvester agent
        harvester = TranscriptHarvesterAgent()

        # Determine priority based on source
        if source in ("discord", "42macro"):
            priority = "high"  # Tier 1 - Imran's videos, Darius Dale
        else:
            priority = "standard"  # Tier 3 - YouTube, etc.

        # Build metadata
        metadata = {
            "title": title or f"Video from {source}",
            "source": source,
        }

        # Run the harvest pipeline (download -> transcribe -> analyze)
        import asyncio

        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                harvester.harvest(
                    video_url=video_url,
                    source=source,
                    metadata=metadata,
                    priority=priority
                )
            )
        finally:
            loop.close()

        if not result or not result.get("transcript"):
            logger.warning(f"Transcription returned no transcript for {raw_content_id}")
            return False

        # Update database with transcript
        db = SessionLocal()
        raw_content = db.query(RawContent).filter(RawContent.id == raw_content_id).first()

        if not raw_content:
            logger.error(f"RawContent {raw_content_id} not found for transcript update")
            return False

        # Parse existing metadata
        existing_metadata = json.loads(raw_content.json_metadata or "{}")

        # Add transcript data to metadata
        existing_metadata["transcript"] = result["transcript"]
        existing_metadata["transcription_duration"] = result.get("video_duration_seconds")
        existing_metadata["transcribed_at"] = datetime.utcnow().isoformat()
        existing_metadata["transcription_sentiment"] = result.get("sentiment")
        existing_metadata["transcription_conviction"] = result.get("conviction")
        existing_metadata["transcription_themes"] = result.get("key_themes", [])

        # Update the record
        raw_content.json_metadata = json.dumps(existing_metadata)
        raw_content.content_text = result["transcript"]  # Store transcript as main content

        db.commit()

        transcript_len = len(result["transcript"])
        logger.info(f"Transcription complete for {raw_content_id}: {transcript_len} chars, sentiment={result.get('sentiment')}")

        return True

    except ImportError as e:
        logger.error(f"TranscriptHarvesterAgent not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Transcription failed for {raw_content_id}: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False
    finally:
        if db:
            db.close()


async def _transcribe_video_async(
    raw_content_id: int,
    video_url: str,
    source: str,
    title: Optional[str] = None
):
    """
    Run video transcription in background thread pool.

    PRD-018: Async wrapper to avoid blocking the event loop.

    Args:
        raw_content_id: ID of the RawContent record
        video_url: URL of the video
        source: Source name
        title: Optional title
    """
    loop = asyncio.get_event_loop()

    try:
        await loop.run_in_executor(
            transcription_executor,
            _transcribe_video_sync,
            raw_content_id,
            video_url,
            source,
            title
        )
    except Exception as e:
        logger.error(f"Async transcription wrapper failed: {e}")


@router.post("/discord")
async def ingest_discord_data(
    messages: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """
    Receive Discord messages from local laptop collector script.

    This endpoint is called by scripts/discord_local.py running on Sebastian's laptop.

    Args:
        messages: List of Discord messages with metadata
        db: Database session

    Returns:
        Ingestion result with count of saved messages
    """
    if not messages:
        return {
            "status": "success",
            "message": "No messages to ingest",
            "saved": 0
        }

    try:
        # Get or create Discord source
        source = db.query(Source).filter(Source.name == "discord").first()
        if not source:
            source = Source(
                name="discord",
                type="discord",
                active=True,
                last_collected_at=datetime.utcnow()
            )
            db.add(source)
            db.commit()
            db.refresh(source)
        else:
            # Update last collected time
            source.last_collected_at = datetime.utcnow()

        # Save each message as raw content
        saved_count = 0
        skipped_duplicates = 0
        errors = []
        videos_to_transcribe = []  # PRD-018: Track videos needing transcription

        for idx, message_data in enumerate(messages):
            try:
                # Validate required fields
                if "content_type" not in message_data:
                    error_msg = f"Message {idx}: Missing content_type"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue

                # Check for duplicates by message_id or URL
                metadata = message_data.get("metadata", {})
                message_id = metadata.get("message_id")
                url = message_data.get("url")

                if check_duplicate(db, source.id, url=url, message_id=message_id):
                    skipped_duplicates += 1
                    logger.debug(f"Skipping duplicate message: {message_id or url}")
                    continue

                # Parse collected_at if it's a string
                collected_at = message_data.get("collected_at", datetime.utcnow())
                if isinstance(collected_at, str):
                    from dateutil.parser import parse as parse_datetime
                    collected_at = parse_datetime(collected_at)

                raw_content = RawContent(
                    source_id=source.id,
                    content_type=message_data["content_type"],
                    content_text=message_data.get("content_text"),
                    file_path=message_data.get("file_path"),
                    url=message_data.get("url"),
                    json_metadata=json.dumps(message_data.get("metadata", {})),
                    collected_at=collected_at,
                    processed=False
                )

                db.add(raw_content)
                db.flush()  # PRD-018: Get the ID immediately for transcription tracking

                # PRD-018: Check if video needs transcription
                if message_data["content_type"] == "video" and url:
                    # Check if local collector already transcribed this
                    video_transcripts = metadata.get("video_transcripts", [])
                    has_local_transcript = any(
                        t.get("transcript") for t in video_transcripts
                    )

                    if not has_local_transcript:
                        # Queue for server-side transcription
                        videos_to_transcribe.append({
                            "raw_content_id": raw_content.id,
                            "url": url,
                            "title": metadata.get("title") or message_data.get("content_text", "")[:100]
                        })
                        logger.info(f"Queued video for transcription: {url[:50]}...")

                saved_count += 1
                logger.info(f"Added message {idx} to session: {message_data.get('content_type')}")

            except Exception as e:
                import traceback
                error_msg = f"Message {idx}: {str(e)}\n{traceback.format_exc()}"
                logger.error(f"Error saving Discord message: {error_msg}")
                errors.append(error_msg)
                continue

        # Commit all changes
        db.commit()
        logger.info(f"Committed {saved_count}/{len(messages)} Discord messages to database (skipped {skipped_duplicates} duplicates)")

        # Verify the commit worked
        count_after = db.query(RawContent).filter(RawContent.source_id == source.id).count()
        logger.info(f"Total RawContent for source {source.id} after commit: {count_after}")

        # PRD-018: Trigger async transcription for videos without local transcripts
        transcription_queued = 0
        for video in videos_to_transcribe:
            try:
                asyncio.create_task(_transcribe_video_async(
                    raw_content_id=video["raw_content_id"],
                    video_url=video["url"],
                    source="discord",
                    title=video["title"]
                ))
                transcription_queued += 1
            except Exception as e:
                logger.error(f"Failed to queue transcription for {video['raw_content_id']}: {e}")

        if transcription_queued > 0:
            logger.info(f"Queued {transcription_queued} videos for async transcription")

        response = {
            "status": "success",
            "message": f"Ingested {saved_count} Discord messages",
            "saved": saved_count,
            "received": len(messages),
            "skipped_duplicates": skipped_duplicates,
            "transcription_queued": transcription_queued,  # PRD-018
            "total_in_db": count_after,
            "timestamp": datetime.utcnow().isoformat()
        }

        if errors:
            response["errors"] = errors

        return response

    except Exception as e:
        db.rollback()
        logger.error(f"Discord ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/42macro")
async def ingest_42macro_data(
    items: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """
    Receive 42 Macro content from local laptop collector script.

    This endpoint is called by dev/scripts/macro42_local.py running on Sebastian's laptop.
    42macro requires Selenium/Chrome which isn't available on Railway.

    Args:
        items: List of PDFs and videos with metadata
        db: Database session

    Returns:
        Ingestion result with count of saved items
    """
    if not items:
        return {
            "status": "success",
            "message": "No items to ingest",
            "saved": 0
        }

    try:
        # Get or create 42macro source
        source = db.query(Source).filter(Source.name == "42macro").first()
        if not source:
            source = Source(
                name="42macro",
                type="42macro",
                active=True,
                last_collected_at=datetime.utcnow()
            )
            db.add(source)
            db.commit()
            db.refresh(source)
        else:
            # Update last collected time
            source.last_collected_at = datetime.utcnow()

        # Save each item as raw content
        saved_count = 0
        skipped_duplicates = 0
        errors = []
        videos_to_transcribe = []  # PRD-018: Track videos needing transcription

        for idx, item_data in enumerate(items):
            try:
                # Validate required fields
                if "content_type" not in item_data:
                    error_msg = f"Item {idx}: Missing content_type"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    continue

                # Check for duplicates by URL, video_id, or report_type+date
                metadata = item_data.get("metadata", {})
                url = item_data.get("url")
                video_id = metadata.get("video_id")
                report_type = metadata.get("report_type")
                date = metadata.get("date")

                if check_duplicate(
                    db, source.id,
                    url=url,
                    video_id=video_id,
                    report_type=report_type,
                    date=date
                ):
                    skipped_duplicates += 1
                    logger.debug(f"Skipping duplicate 42macro item: {url or video_id or f'{report_type} - {date}'}")
                    continue

                # Parse collected_at if it's a string
                collected_at = item_data.get("collected_at", datetime.utcnow())
                if isinstance(collected_at, str):
                    from dateutil.parser import parse as parse_datetime
                    collected_at = parse_datetime(collected_at)

                raw_content = RawContent(
                    source_id=source.id,
                    content_type=item_data["content_type"],
                    content_text=item_data.get("content_text"),
                    file_path=item_data.get("file_path"),
                    url=item_data.get("url"),
                    json_metadata=json.dumps(item_data.get("metadata", {})),
                    collected_at=collected_at,
                    processed=False
                )

                db.add(raw_content)
                db.flush()  # PRD-018: Get the ID immediately for transcription tracking

                # PRD-018: Queue video content for transcription
                if item_data["content_type"] == "video" and url:
                    videos_to_transcribe.append({
                        "raw_content_id": raw_content.id,
                        "url": url,
                        "title": metadata.get("title") or f"{report_type} - {date}" if report_type else ""
                    })
                    logger.info(f"Queued 42macro video for transcription: {url[:50]}...")

                saved_count += 1
                logger.info(f"Added 42macro item {idx}: {item_data.get('content_type')}")

            except Exception as e:
                import traceback
                error_msg = f"Item {idx}: {str(e)}\n{traceback.format_exc()}"
                logger.error(f"Error saving 42macro item: {error_msg}")
                errors.append(error_msg)
                continue

        # Commit all changes
        db.commit()
        logger.info(f"Committed {saved_count}/{len(items)} 42macro items to database (skipped {skipped_duplicates} duplicates)")

        # Verify the commit worked
        count_after = db.query(RawContent).filter(RawContent.source_id == source.id).count()
        logger.info(f"Total RawContent for 42macro after commit: {count_after}")

        # PRD-018: Trigger async transcription for videos
        transcription_queued = 0
        for video in videos_to_transcribe:
            try:
                asyncio.create_task(_transcribe_video_async(
                    raw_content_id=video["raw_content_id"],
                    video_url=video["url"],
                    source="42macro",
                    title=video["title"]
                ))
                transcription_queued += 1
            except Exception as e:
                logger.error(f"Failed to queue transcription for {video['raw_content_id']}: {e}")

        if transcription_queued > 0:
            logger.info(f"Queued {transcription_queued} 42macro videos for async transcription")

        response = {
            "status": "success",
            "message": f"Ingested {saved_count} 42macro items",
            "saved": saved_count,
            "received": len(items),
            "skipped_duplicates": skipped_duplicates,
            "transcription_queued": transcription_queued,  # PRD-018
            "total_in_db": count_after,
            "timestamp": datetime.utcnow().isoformat()
        }

        if errors:
            response["errors"] = errors

        return response

    except Exception as e:
        db.rollback()
        logger.error(f"42macro ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/{source_name}")
async def trigger_collection(
    source_name: str,
    db: Session = Depends(get_db)
):
    """
    Manually trigger collection from a specific source.

    Args:
        source_name: Name of source to collect from (e.g., "42macro", "youtube")
        db: Database session

    Returns:
        Collection trigger confirmation
    """
    valid_sources = ["42macro", "discord", "twitter", "youtube", "substack", "kt_technical"]

    if source_name not in valid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source. Must be one of: {', '.join(valid_sources)}"
        )

    # For Discord, this is handled by the local script
    if source_name == "discord":
        return {
            "status": "info",
            "message": "Discord collection runs locally on your laptop via scheduled task",
            "instructions": "Run: python scripts/discord_local.py"
        }

    # For Twitter, collection is disabled due to API rate limits
    if source_name == "twitter":
        return {
            "status": "info",
            "message": "Twitter collection is disabled (API rate limits on free tier)",
            "instructions": "Manually input tweets via dashboard if needed"
        }

    # Run collection in background for supported sources
    try:
        collected_items = await _run_collector(source_name)

        # Save collected items to database
        saved_count = await _save_collected_items(db, source_name, collected_items)

        return {
            "status": "success",
            "message": f"Collected {len(collected_items)} items from {source_name}",
            "saved": saved_count,
            "source": source_name,
            "timestamp": datetime.utcnow().isoformat()
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Collection failed for {source_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Collection failed: {str(e)}")


async def _run_collector(source_name: str) -> List[Dict[str, Any]]:
    """
    Initialize and run the appropriate collector.

    Args:
        source_name: Name of source to collect from

    Returns:
        List of collected content items
    """
    if source_name == "youtube":
        from collectors.youtube_api import YouTubeCollector

        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            raise ValueError("YOUTUBE_API_KEY not configured")

        collector = YouTubeCollector(api_key=api_key)
        return await collector.collect()

    elif source_name == "substack":
        from collectors.substack_rss import SubstackCollector

        collector = SubstackCollector()
        return await collector.collect()

    elif source_name == "42macro":
        from collectors.macro42_selenium import Macro42Collector

        email = os.getenv("MACRO42_EMAIL")
        password = os.getenv("MACRO42_PASSWORD")
        if not email or not password:
            raise ValueError("MACRO42_EMAIL and MACRO42_PASSWORD not configured")

        collector = Macro42Collector(email=email, password=password, headless=True)
        return await collector.collect()

    elif source_name == "kt_technical":
        from collectors.kt_technical import KTTechnicalCollector

        # Credentials default to env vars in the collector
        collector = KTTechnicalCollector()
        return await collector.collect()

    else:
        raise ValueError(f"Unknown source: {source_name}")


async def _save_collected_items(
    db: Session,
    source_name: str,
    items: List[Dict[str, Any]]
) -> int:
    """
    Save collected items to database.

    Args:
        db: Database session
        source_name: Name of the source
        items: List of collected content items

    Returns:
        Number of items saved
    """
    if not items:
        return 0

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
    videos_to_transcribe = []  # PRD-018: Track videos needing transcription

    for item in items:
        try:
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
                from dateutil.parser import parse as parse_datetime
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
            db.flush()  # PRD-018: Get ID for transcription tracking

            # PRD-018: Queue video content for transcription (YouTube, etc.)
            if item.get("content_type") == "video" and url:
                videos_to_transcribe.append({
                    "raw_content_id": raw_content.id,
                    "url": url,
                    "title": metadata.get("title") or item.get("content_text", "")[:100]
                })

            saved_count += 1
        except Exception as e:
            logger.error(f"Error saving item from {source_name}: {e}")
            continue

    db.commit()
    if skipped_duplicates > 0:
        logger.info(f"Saved {saved_count}/{len(items)} items from {source_name} (skipped {skipped_duplicates} duplicates)")
    else:
        logger.info(f"Saved {saved_count}/{len(items)} items from {source_name}")

    # PRD-018: Trigger async transcription for video content
    transcription_queued = 0
    for video in videos_to_transcribe:
        try:
            asyncio.create_task(_transcribe_video_async(
                raw_content_id=video["raw_content_id"],
                video_url=video["url"],
                source=source_name,
                title=video["title"]
            ))
            transcription_queued += 1
        except Exception as e:
            logger.error(f"Failed to queue transcription for {video['raw_content_id']}: {e}")

    if transcription_queued > 0:
        logger.info(f"Queued {transcription_queued} videos from {source_name} for async transcription")

    return saved_count


@router.get("/status")
async def get_collection_status(db: Session = Depends(get_db)):
    """
    Get collection status for all sources.

    Returns:
        Status of all data sources
    """
    try:
        sources = db.query(Source).all()

        status_list = []
        for source in sources:
            # Count raw content
            raw_count = db.query(RawContent).filter(
                RawContent.source_id == source.id
            ).count()

            # Count unprocessed
            unprocessed_count = db.query(RawContent).filter(
                RawContent.source_id == source.id,
                RawContent.processed == False
            ).count()

            status_list.append({
                "source": source.name,
                "type": source.type,
                "active": source.active,
                "last_collected_at": source.last_collected_at.isoformat() if source.last_collected_at else None,
                "total_content": raw_count,
                "unprocessed": unprocessed_count
            })

        return {
            "sources": status_list,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get collection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{source_name}")
async def get_source_stats(
    source_name: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a specific source.

    Args:
        source_name: Name of the source

    Returns:
        Detailed statistics
    """
    try:
        source = db.query(Source).filter(Source.name == source_name).first()

        if not source:
            raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found")

        # Get content by type
        content_by_type = {}
        types = ["text", "pdf", "video", "image"]

        for content_type in types:
            count = db.query(RawContent).filter(
                RawContent.source_id == source.id,
                RawContent.content_type == content_type
            ).count()
            content_by_type[content_type] = count

        # Get recent collection dates
        recent_content = db.query(RawContent.collected_at).filter(
            RawContent.source_id == source.id
        ).order_by(RawContent.collected_at.desc()).limit(10).all()

        recent_dates = [c.collected_at.isoformat() for c in recent_content]

        return {
            "source": source_name,
            "type": source.type,
            "active": source.active,
            "last_collected_at": source.last_collected_at.isoformat() if source.last_collected_at else None,
            "content_by_type": content_by_type,
            "recent_collections": recent_dates,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get source stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear/{source_name}")
async def clear_source_data(
    source_name: str,
    db: Session = Depends(get_db)
):
    """
    Clear all collected data for a specific source.

    Use this to remove stale/duplicate data before re-collecting.
    Protected by HTTP Basic Auth.

    Args:
        source_name: Name of source to clear (e.g., "youtube", "substack")

    Returns:
        Count of deleted items
    """
    valid_sources = ["42macro", "discord", "twitter", "youtube", "substack", "kt_technical"]

    if source_name not in valid_sources:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source. Must be one of: {', '.join(valid_sources)}"
        )

    try:
        source = db.query(Source).filter(Source.name == source_name).first()

        if not source:
            return {
                "status": "success",
                "message": f"Source '{source_name}' not found (nothing to clear)",
                "deleted": 0
            }

        # Count items before deletion
        count = db.query(RawContent).filter(RawContent.source_id == source.id).count()

        # Delete all content for this source
        db.query(RawContent).filter(RawContent.source_id == source.id).delete()

        # Reset last_collected_at so fresh collection works
        source.last_collected_at = None

        db.commit()

        logger.info(f"Cleared {count} items from {source_name}")

        return {
            "status": "success",
            "message": f"Cleared all data for {source_name}",
            "deleted": count,
            "source": source_name,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clear source data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
