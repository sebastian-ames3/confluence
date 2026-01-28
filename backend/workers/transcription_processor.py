"""
Background Transcription Processor

PRD-052: Reliable background processing for video transcriptions.

This processor runs as a background task and picks up pending transcriptions
from the TranscriptionStatus table. It processes them reliably even if the
original HTTP request that queued them has completed.

The processor runs on startup and periodically checks for pending items.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Configuration
PROCESSOR_INTERVAL_SECONDS = int(os.getenv("TRANSCRIPTION_PROCESSOR_INTERVAL", "60"))
MAX_CONCURRENT_TRANSCRIPTIONS = int(os.getenv("MAX_CONCURRENT_TRANSCRIPTIONS", "2"))
MAX_RETRIES = int(os.getenv("TRANSCRIPTION_MAX_RETRIES", "3"))
STALE_PROCESSING_THRESHOLD_MINUTES = 30  # Mark "processing" items as stuck after this


class TranscriptionProcessor:
    """Background processor for pending video transcriptions."""

    def __init__(self):
        self.running = False
        self.current_tasks = 0
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the background processor."""
        if self.running:
            logger.warning("Transcription processor already running")
            return

        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Transcription processor started (interval: {PROCESSOR_INTERVAL_SECONDS}s, max concurrent: {MAX_CONCURRENT_TRANSCRIPTIONS})")

    async def stop(self):
        """Stop the background processor."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Transcription processor stopped")

    async def _run_loop(self):
        """Main processing loop."""
        # Wait a bit on startup to let the app initialize
        await asyncio.sleep(10)

        while self.running:
            try:
                await self._process_pending()
            except Exception as e:
                logger.error(f"Error in transcription processor loop: {e}")

            # Wait before next check
            await asyncio.sleep(PROCESSOR_INTERVAL_SECONDS)

    async def _process_pending(self):
        """Find and process pending transcriptions."""
        from backend.models import get_async_db, TranscriptionStatus, RawContent
        import json

        async for db in get_async_db():
            try:
                # First, recover any stuck "processing" items
                await self._recover_stuck_items(db)

                # Find pending items that can be processed
                available_slots = MAX_CONCURRENT_TRANSCRIPTIONS - self.current_tasks
                if available_slots <= 0:
                    logger.debug(f"No available slots (current: {self.current_tasks})")
                    return

                # Query pending items, prioritizing older ones
                stmt = (
                    select(TranscriptionStatus, RawContent)
                    .join(RawContent, TranscriptionStatus.content_id == RawContent.id)
                    .where(
                        and_(
                            TranscriptionStatus.status == "pending",
                            TranscriptionStatus.retry_count < MAX_RETRIES
                        )
                    )
                    .order_by(TranscriptionStatus.created_at)
                    .limit(available_slots)
                )

                result = await db.execute(stmt)
                items = result.all()

                if not items:
                    logger.debug("No pending transcriptions to process")
                    return

                logger.info(f"Found {len(items)} pending transcriptions to process")

                # Process each item
                for status, raw_content in items:
                    # Mark as processing first
                    status.status = "processing"
                    status.last_attempt_at = datetime.utcnow()
                    await db.commit()

                    # Start transcription in background
                    asyncio.create_task(
                        self._transcribe_item(status.id, raw_content)
                    )
                    self.current_tasks += 1

            except Exception as e:
                logger.error(f"Error processing pending transcriptions: {e}")
            finally:
                break  # Exit the async generator

    async def _recover_stuck_items(self, db: AsyncSession):
        """Reset items stuck in 'processing' state."""
        from backend.models import TranscriptionStatus

        cutoff = datetime.utcnow() - timedelta(minutes=STALE_PROCESSING_THRESHOLD_MINUTES)

        stmt = (
            update(TranscriptionStatus)
            .where(
                and_(
                    TranscriptionStatus.status == "processing",
                    TranscriptionStatus.last_attempt_at < cutoff
                )
            )
            .values(status="pending", error_message="Reset from stuck processing state")
        )

        result = await db.execute(stmt)
        if result.rowcount > 0:
            logger.warning(f"Reset {result.rowcount} stuck transcriptions from 'processing' to 'pending'")
            await db.commit()

    async def _transcribe_item(self, status_id: int, raw_content):
        """Transcribe a single item."""
        from backend.models import get_async_db, TranscriptionStatus, RawContent, AnalyzedContent, Source
        from agents.transcript_harvester import TranscriptHarvesterAgent
        import json

        try:
            logger.info(f"Starting transcription for status_id={status_id}, content_id={raw_content.id}")

            # Parse metadata
            metadata = {}
            if raw_content.json_metadata:
                try:
                    metadata = json.loads(raw_content.json_metadata)
                except json.JSONDecodeError:
                    pass

            # Get video URL
            video_url = raw_content.url or metadata.get("url") or metadata.get("video_url")
            if not video_url:
                raise ValueError("No video URL found")

            # Get source name
            source_name = "unknown"
            async for db in get_async_db():
                try:
                    result = await db.execute(
                        select(Source).where(Source.id == raw_content.source_id)
                    )
                    source = result.scalar_one_or_none()
                    if source:
                        source_name = source.name
                finally:
                    break

            # Run transcription
            harvester = TranscriptHarvesterAgent()
            result = harvester.process_video(
                video_url=video_url,
                source=source_name,
                title=metadata.get("title", ""),
                source_metadata=metadata
            )

            # Update database with results
            async for db in get_async_db():
                try:
                    # Get status record
                    status_result = await db.execute(
                        select(TranscriptionStatus).where(TranscriptionStatus.id == status_id)
                    )
                    status = status_result.scalar_one_or_none()

                    if not status:
                        logger.error(f"TranscriptionStatus {status_id} not found")
                        return

                    if result and result.get("transcript"):
                        # Success - update raw content with transcript
                        await db.execute(
                            update(RawContent)
                            .where(RawContent.id == raw_content.id)
                            .values(content_text=result["transcript"])
                        )

                        # Create AnalyzedContent record
                        analyzed = AnalyzedContent(
                            raw_content_id=raw_content.id,
                            agent_type="transcript",
                            key_themes=",".join(result.get("themes", [])),
                            tickers_mentioned=",".join(result.get("tickers", [])),
                            sentiment=result.get("sentiment"),
                            conviction=result.get("conviction"),
                            analysis_result=json.dumps(result.get("analysis", {})),
                            analyzed_at=datetime.utcnow()
                        )
                        db.add(analyzed)

                        # Update status
                        status.status = "completed"
                        status.completed_at = datetime.utcnow()
                        status.error_message = None

                        logger.info(f"Transcription completed for content_id={raw_content.id}: {len(result['transcript'])} chars")
                    else:
                        # No transcript returned
                        status.status = "failed"
                        status.error_message = "No transcript returned from harvester"
                        status.retry_count += 1
                        logger.warning(f"Transcription returned no transcript for content_id={raw_content.id}")

                    await db.commit()
                finally:
                    break

        except Exception as e:
            logger.error(f"Transcription failed for status_id={status_id}: {e}")

            # Update status to failed
            async for db in get_async_db():
                try:
                    await db.execute(
                        update(TranscriptionStatus)
                        .where(TranscriptionStatus.id == status_id)
                        .values(
                            status="failed",
                            error_message=str(e)[:500],
                            retry_count=TranscriptionStatus.retry_count + 1
                        )
                    )
                    await db.commit()
                finally:
                    break

        finally:
            self.current_tasks -= 1


# Global processor instance
_processor: Optional[TranscriptionProcessor] = None


def get_processor() -> TranscriptionProcessor:
    """Get or create the global processor instance."""
    global _processor
    if _processor is None:
        _processor = TranscriptionProcessor()
    return _processor


async def start_processor():
    """Start the background transcription processor."""
    processor = get_processor()
    await processor.start()


async def stop_processor():
    """Stop the background transcription processor."""
    processor = get_processor()
    await processor.stop()
