"""
Deduplication utilities for content collection.

Provides consistent duplicate detection across all collection paths.
"""

from sqlalchemy.orm import Session
from backend.models import RawContent
import logging

logger = logging.getLogger(__name__)


def check_duplicate(
    db: Session,
    source_id: int,
    url: str = None,
    message_id: str = None,
    video_id: str = None,
    report_type: str = None,
    date: str = None
) -> bool:
    """
    Check if content already exists in database.

    Args:
        db: Database session
        source_id: ID of the source
        url: Content URL (for Substack, KT Technical, etc.)
        message_id: Discord message ID
        video_id: YouTube or Vimeo video ID
        report_type: 42 Macro report type (e.g., "Around The Horn")
        date: 42 Macro report date

    Returns:
        True if duplicate found, False if new content.
    """
    # Check by URL (most common - Substack, KT Technical, general)
    if url:
        existing = db.query(RawContent).filter(
            RawContent.source_id == source_id,
            RawContent.url == url
        ).first()
        if existing:
            logger.debug(f"Duplicate found by URL: {url}")
            return True

    # Check by message_id (Discord)
    if message_id:
        existing = db.query(RawContent).filter(
            RawContent.source_id == source_id,
            RawContent.json_metadata.contains(f'"message_id": "{message_id}"')
        ).first()
        if existing:
            logger.debug(f"Duplicate found by message_id: {message_id}")
            return True

    # Check by video_id (YouTube, Vimeo)
    if video_id:
        existing = db.query(RawContent).filter(
            RawContent.source_id == source_id,
            RawContent.json_metadata.contains(f'"video_id": "{video_id}"')
        ).first()
        if existing:
            logger.debug(f"Duplicate found by video_id: {video_id}")
            return True

    # Check by report_type + date (42 Macro PDFs)
    if report_type and date:
        existing = db.query(RawContent).filter(
            RawContent.source_id == source_id,
            RawContent.json_metadata.contains(f'"report_type": "{report_type}"'),
            RawContent.json_metadata.contains(f'"date": "{date}"')
        ).first()
        if existing:
            logger.debug(f"Duplicate found by report_type+date: {report_type} - {date}")
            return True

    return False


def add_dedup_indexes(db_engine):
    """
    Add database indexes for efficient duplicate lookups.
    
    Should be called once during database initialization or migration.
    """
    from sqlalchemy import text
    
    with db_engine.connect() as conn:
        # Add index on (source_id, url) for fast URL lookups
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_source_url
            ON raw_content (source_id, url)
        """))

        # Add index on (source_id, content_type) for filtering
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_source_content_type
            ON raw_content (source_id, content_type)
        """))

        conn.commit()
        logger.info("Added deduplication indexes to raw_content table")
