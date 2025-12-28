"""
Backfill Discord Image URLs

One-time script to populate URL field for existing Discord images
that were collected before URL storage was added.

Attempts to extract URL from json_metadata if available.

Usage:
    python scripts/backfill_discord_image_urls.py
"""

import json
import logging
from backend.models import SessionLocal, RawContent, Source

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def backfill_urls():
    """Find Discord images without URLs and try to populate from metadata."""
    db = SessionLocal()

    try:
        # Get Discord source
        discord_source = db.query(Source).filter(Source.name == "discord").first()
        if not discord_source:
            logger.error("Discord source not found")
            return

        # Find images without URLs
        images = db.query(RawContent).filter(
            RawContent.source_id == discord_source.id,
            RawContent.content_type == "image",
            RawContent.url.is_(None)
        ).all()

        logger.info(f"Found {len(images)} Discord images without URLs")

        updated = 0
        for img in images:
            # Try to extract URL from metadata
            if img.json_metadata:
                try:
                    metadata = json.loads(img.json_metadata)

                    # Check attachments for URL
                    attachments = metadata.get("attachments", [])
                    for att in attachments:
                        if att.get("type") == "image" and att.get("url"):
                            img.url = att["url"]
                            updated += 1
                            logger.info(f"Updated ID {img.id}: {att['url'][:60]}...")
                            break
                except json.JSONDecodeError:
                    pass

        db.commit()
        logger.info(f"Backfill complete: {updated}/{len(images)} images updated with URLs")

    finally:
        db.close()


if __name__ == "__main__":
    backfill_urls()
