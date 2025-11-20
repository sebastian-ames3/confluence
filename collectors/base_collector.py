"""
Base Collector Class

Foundation for all data collectors.
Provides common functionality for collecting content from various sources.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
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
    """

    def __init__(self, source_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base collector.

        Args:
            source_name: Name of the data source (e.g., "discord", "42macro")
            config: Optional configuration dictionary
        """
        self.source_name = source_name
        self.config = config or {}
        self.download_dir = Path(f"downloads/{source_name}")
        self.download_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized {self.__class__.__name__} for source '{source_name}'")

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
        valid_types = ["text", "pdf", "video", "image", "article", "tweet", "chart", "post"]
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
            content["collected_at"] = datetime.utcnow().isoformat()

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

        Args:
            content_items: List of content items to save

        Returns:
            Number of items successfully saved
        """
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
            for content in content_items:
                if not self.validate_content(content):
                    logger.warning(f"Skipping invalid content: {content.get('content_text', '')[:50]}")
                    continue

                prepared = self.prepare_for_database(content)

                raw_content = RawContent(
                    source_id=source.id,
                    content_type=prepared["content_type"],
                    content_text=prepared.get("content_text"),
                    file_path=prepared.get("file_path"),
                    url=prepared.get("url"),
                    json_metadata=json.dumps(prepared.get("metadata", {})),
                    processed=False
                )

                db.add(raw_content)
                saved_count += 1

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

        Returns:
            Summary of collection results
        """
        start_time = datetime.now()
        logger.info(f"Starting collection for {self.source_name}...")

        try:
            # Collect content
            content_items = await self.collect()

            # Save to database
            saved_count = await self.save_to_database(content_items)

            elapsed_time = (datetime.now() - start_time).total_seconds()

            result = {
                "source": self.source_name,
                "status": "success",
                "collected": len(content_items),
                "saved": saved_count,
                "elapsed_seconds": round(elapsed_time, 2),
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(
                f"Collection complete: {saved_count}/{len(content_items)} items saved "
                f"in {elapsed_time:.2f}s"
            )

            return result

        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Collection failed for {self.source_name}: {str(e)}")

            return {
                "source": self.source_name,
                "status": "error",
                "error": str(e),
                "elapsed_seconds": round(elapsed_time, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
