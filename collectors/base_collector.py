"""
Base Collector Class

Foundation for all data collectors.
Provides common functionality for collecting content from various sources.

PRD-034: Added dry_run mode for testing collectors without database writes.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Abstract base class for all content collectors.

    Provides:
    - Standard collection interface
    - Error handling and retry logic
    - Data validation
    - Database integration
    - Dry-run mode for testing (PRD-034)
    """

    def __init__(
        self,
        source_name: str,
        config: Optional[Dict[str, Any]] = None,
        dry_run: bool = False
    ):
        """
        Initialize base collector.

        Args:
            source_name: Name of the data source (e.g., "discord", "42macro")
            config: Optional configuration dictionary
            dry_run: If True, skip database writes and log what would be saved (PRD-034)
        """
        self.source_name = source_name
        self.config = config or {}
        self.dry_run = dry_run
        self.download_dir = Path(f"downloads/{source_name}")
        self.download_dir.mkdir(parents=True, exist_ok=True)

        mode_str = " [DRY RUN]" if dry_run else ""
        logger.info(f"Initialized {self.__class__.__name__} for source '{source_name}'{mode_str}")

    @abstractmethod
    async def collect(self) -> List[Dict[str, Any]]:
        """
        Main collection method to be implemented by subclasses.

        Returns:
            List of collected content items

        Raises:
            NotImplementedError: Must be implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement collect() method")

    def validate_content(self, content: Dict[str, Any]) -> bool:
        """
        Validate collected content before saving.

        Args:
            content: Content dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["content_type", "collected_at"]

        for field in required_fields:
            if field not in content:
                logger.warning(f"Content missing required field: {field}")
                return False

        # Content type must be valid
        valid_types = ["text", "pdf", "video", "image", "article", "tweet", "chart", "post", "blog_post"]
        if content["content_type"] not in valid_types:
            logger.warning(f"Invalid content type: {content['content_type']}")
            return False

        return True

    def prepare_for_database(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare collected content for database insertion.

        Args:
            content: Raw collected content

        Returns:
            Content formatted for database
        """
        # Ensure required fields exist
        if "collected_at" not in content:
            content["collected_at"] = datetime.now(timezone.utc).isoformat()

        # Add source name
        content["source"] = self.source_name

        # Ensure metadata is present
        if "metadata" not in content:
            content["metadata"] = {}

        # Add collection metadata
        content["metadata"]["collector_version"] = "1.0"
        content["metadata"]["collection_timestamp"] = content["collected_at"]

        return content

    async def save_to_database(self, content_items: List[Dict[str, Any]]) -> int:
        """
        Save collected content to database.

        PRD-034: Supports dry_run mode - logs what would be saved without writing.

        Args:
            content_items: List of content items to save

        Returns:
            Number of items successfully saved (or would be saved in dry_run mode)
        """
        # PRD-034: Dry-run mode - log what would be saved without writing
        if self.dry_run:
            logger.info(f"[DRY RUN] Would save {len(content_items)} items to database")
            for i, item in enumerate(content_items[:3]):  # Log first 3 items as sample
                url = item.get("url", "no-url")[:100]
                content_type = item.get("content_type", "unknown")
                logger.info(f"[DRY RUN] Sample item {i+1}: type={content_type}, url={url}")
            if len(content_items) > 3:
                logger.info(f"[DRY RUN] ... and {len(content_items) - 3} more items")
            return len(content_items)

        from sqlalchemy.orm import Session
        from backend.models import SessionLocal, RawContent, Source
        import json

        saved_count = 0
        db: Session = SessionLocal()

        try:
            # Get or create source record
            source = db.query(Source).filter(Source.name == self.source_name).first()
            if not source:
                source = Source(
                    name=self.source_name,
                    type=self._get_source_type(),
                    active=True
                )
                db.add(source)
                db.commit()
                db.refresh(source)

            # Save each content item
            skipped_duplicates = 0
            for content in content_items:
                if not self.validate_content(content):
                    logger.warning(f"Skipping invalid content: {content.get('content_text', '')[:50]}")
                    continue

                prepared = self.prepare_for_database(content)
                metadata = prepared.get("metadata", {})

                # Check for duplicate by message_id (Discord) or url (other sources)
                message_id = metadata.get("message_id")
                url = prepared.get("url")

                if message_id:
                    # Check if this message_id already exists for this source
                    existing = db.query(RawContent).filter(
                        RawContent.source_id == source.id,
                        RawContent.json_metadata.contains(f'"message_id": "{message_id}"')
                    ).first()
                    if existing:
                        skipped_duplicates += 1
                        continue
                elif url:
                    # Check if this URL already exists for this source
                    existing = db.query(RawContent).filter(
                        RawContent.source_id == source.id,
                        RawContent.url == url
                    ).first()
                    if existing:
                        skipped_duplicates += 1
                        continue

                raw_content = RawContent(
                    source_id=source.id,
                    content_type=prepared["content_type"],
                    content_text=prepared.get("content_text"),
                    file_path=prepared.get("file_path"),
                    url=prepared.get("url"),
                    json_metadata=json.dumps(metadata),
                    processed=False
                )

                db.add(raw_content)
                saved_count += 1

            if skipped_duplicates > 0:
                logger.info(f"Skipped {skipped_duplicates} duplicate items")

            # Update last_collected_at to prevent duplicate collection
            if saved_count > 0:
                source.last_collected_at = datetime.now(timezone.utc)

            db.commit()
            logger.info(f"Saved {saved_count} items to database")

        except Exception as e:
            db.rollback()
            logger.error(f"Error saving to database: {str(e)}")
            raise

        finally:
            db.close()

        return saved_count

    def _get_source_type(self) -> str:
        """Get source type for database."""
        type_mapping = {
            "discord": "discord",
            "42macro": "web",
            "twitter": "twitter",
            "youtube": "youtube",
            "substack": "rss"
        }
        return type_mapping.get(self.source_name, "web")

    async def run(self) -> Dict[str, Any]:
        """
        Run the full collection process.

        PRD-034: Includes dry_run flag in result when running in dry-run mode.

        Returns:
            Summary of collection results
        """
        start_time = datetime.now()
        mode_str = " [DRY RUN]" if self.dry_run else ""
        logger.info(f"Starting collection for {self.source_name}{mode_str}...")

        max_retries = self.config.get("max_retries", 3) if self.config else 3
        retry_delay = self.config.get("retry_delay", 5) if self.config else 5

        last_exception = None
        for attempt in range(max_retries):
            try:
                # Collect content
                collection_result = await self.collect()

                # Handle different return formats
                if isinstance(collection_result, dict) and "content" in collection_result:
                    # Twitter-style return with nested content
                    content_items = collection_result["content"]
                elif isinstance(collection_result, list):
                    # Standard list return
                    content_items = collection_result
                else:
                    # Fallback to empty list
                    logger.warning(f"Unexpected collect() return type: {type(collection_result)}")
                    content_items = []

                # Save to database (or simulate in dry-run mode)
                saved_count = await self.save_to_database(content_items)

                elapsed_time = (datetime.now() - start_time).total_seconds()

                result = {
                    "source": self.source_name,
                    "status": "success",
                    "collected": len(content_items),
                    "saved": saved_count,
                    "elapsed_seconds": round(elapsed_time, 2),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "dry_run": self.dry_run  # PRD-034: Include dry_run flag in result
                }

                action_str = "would be saved" if self.dry_run else "saved"
                logger.info(
                    f"Collection complete{mode_str}: {saved_count}/{len(content_items)} items {action_str} "
                    f"in {elapsed_time:.2f}s"
                )

                return result

            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = min(retry_delay * (2 ** attempt), 60)
                    logger.warning(
                        f"Collection attempt {attempt + 1}/{max_retries} failed for "
                        f"{self.source_name}: {e}. Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"Collection failed for {self.source_name} after "
                        f"{max_retries} attempts: {e}"
                    )

        # All retries exhausted - return error result
        elapsed_time = (datetime.now() - start_time).total_seconds()
        return {
            "source": self.source_name,
            "status": "error",
            "error": str(last_exception),
            "elapsed_seconds": round(elapsed_time, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": self.dry_run  # PRD-034: Include dry_run flag in result
        }
