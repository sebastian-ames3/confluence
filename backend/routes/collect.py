"""
Collection Routes

API endpoints for triggering data collection from research sources.
Includes endpoint for receiving Discord data from local laptop script.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging
import json
from datetime import datetime

from backend.models import get_db, RawContent, Source

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collect", tags=["collect"])


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
        for message_data in messages:
            try:
                # Validate required fields
                if "content_type" not in message_data:
                    logger.warning(f"Skipping message without content_type")
                    continue

                raw_content = RawContent(
                    source_id=source.id,
                    content_type=message_data["content_type"],
                    content_text=message_data.get("content_text"),
                    file_path=message_data.get("file_path"),
                    url=message_data.get("url"),
                    json_metadata=json.dumps(message_data.get("metadata", {})),
                    collected_at=message_data.get("collected_at", datetime.utcnow()),
                    processed=False
                )

                db.add(raw_content)
                saved_count += 1

            except Exception as e:
                logger.error(f"Error saving Discord message: {e}")
                continue

        # Commit all changes
        db.commit()

        logger.info(f"Saved {saved_count}/{len(messages)} Discord messages to database")

        return {
            "status": "success",
            "message": f"Ingested {saved_count} Discord messages",
            "saved": saved_count,
            "received": len(messages),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Discord ingestion failed: {e}")
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
    valid_sources = ["42macro", "discord", "twitter", "youtube", "substack"]

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

    # TODO: Implement collection triggers for other sources
    return {
        "status": "pending",
        "message": f"Collection trigger for {source_name} not yet implemented",
        "source": source_name
    }


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
