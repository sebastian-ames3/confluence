"""
Collector Orchestration Script

Runs all configured data collectors and saves results to database.
Can be run manually or via scheduler (6am, 6pm).
"""

import sys
import os
import argparse
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.macro42_selenium import Macro42Collector
from collectors.youtube_api import YouTubeCollector
from collectors.substack_rss import SubstackCollector
from collectors.twitter_api import TwitterCollector
from backend.models import SessionLocal, RawContent, Source
from backend.utils.db import get_or_create_source

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'collector_orchestration.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class CollectorOrchestrator:
    """
    Orchestrates running multiple collectors and saving to database.
    """

    def __init__(self, db_session=None):
        """
        Initialize orchestrator.

        Args:
            db_session: SQLAlchemy session (creates new if not provided)
        """
        self.db = db_session or SessionLocal()
        self.results = {
            'total_collected': 0,
            'by_source': {},
            'errors': []
        }

    async def run_all_collectors(
        self,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run all configured collectors.

        Args:
            sources: List of source names to run. If None, runs all.

        Returns:
            Results summary
        """
        logger.info("=" * 60)
        logger.info("COLLECTOR ORCHESTRATION STARTING")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 60)

        # Default to all sources
        if sources is None:
            sources = ['42macro', 'youtube', 'substack', 'twitter']

        # Run each collector
        for source_name in sources:
            try:
                logger.info(f"\n--- Running {source_name} collector ---")
                await self._run_collector(source_name)
            except Exception as e:
                error_msg = f"Failed to run {source_name} collector: {e}"
                logger.error(error_msg)
                self.results['errors'].append(error_msg)

        # Print summary
        self._print_summary()

        return self.results

    async def _run_collector(self, source_name: str):
        """
        Run a specific collector and save results.

        Args:
            source_name: Name of source/collector to run
        """
        # Get credentials from environment
        collector = None
        content_items = []

        # Initialize appropriate collector
        if source_name == '42macro':
            email = os.getenv('MACRO42_EMAIL')
            password = os.getenv('MACRO42_PASSWORD')

            if not email or not password:
                logger.warning("42macro credentials not found in environment, skipping")
                return

            collector = Macro42Collector(email, password)

        elif source_name == 'youtube':
            api_key = os.getenv('YOUTUBE_API_KEY')

            if not api_key:
                logger.warning("YouTube API key not found in environment, skipping")
                return

            collector = YouTubeCollector(api_key)

        elif source_name == 'substack':
            collector = SubstackCollector()

        elif source_name == 'twitter':
            bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            collector = TwitterCollector(bearer_token=bearer_token)

        else:
            logger.error(f"Unknown source: {source_name}")
            return

        # Collect content
        try:
            content_items = await collector.collect()
            logger.info(f"SUCCESS: Collected {len(content_items)} items from {source_name}")
        except Exception as e:
            error_msg = f"Collection failed for {source_name}: {e}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            return

        # Save to database
        if content_items:
            saved_count = self._save_to_database(source_name, content_items)
            self.results['by_source'][source_name] = saved_count
            self.results['total_collected'] += saved_count
            logger.info(f"Saved {saved_count} items to database")
        else:
            logger.info(f"No new items to save from {source_name}")
            self.results['by_source'][source_name] = 0

    def _save_to_database(
        self,
        source_name: str,
        content_items: List[Dict[str, Any]]
    ) -> int:
        """
        Save collected content to database.

        Args:
            source_name: Name of the source
            content_items: List of content items to save

        Returns:
            Number of items saved
        """
        try:
            # Get or create source
            source = get_or_create_source(self.db, source_name)

            saved_count = 0

            for item in content_items:
                try:
                    # Check for duplicates (by URL if available)
                    url = item.get('url', '')
                    if url:
                        existing = self.db.query(RawContent).filter(
                            RawContent.source_id == source.id,
                            RawContent.url == url
                        ).first()

                        if existing:
                            logger.debug(f"Skipping duplicate: {url}")
                            continue

                    # Create new raw content entry
                    metadata = item.get('metadata', {})
                    raw_content = RawContent(
                        source_id=source.id,
                        content_type=item.get('content_type', 'unknown'),
                        url=item.get('url'),
                        file_path=item.get('file_path'),
                        content_text=item.get('content_text'),
                        json_metadata=json.dumps(metadata) if metadata else None,
                        collected_at=datetime.utcnow()
                    )

                    self.db.add(raw_content)
                    saved_count += 1

                except Exception as e:
                    logger.error(f"Error saving item: {e}")
                    continue

            # Commit all items
            self.db.commit()
            return saved_count

        except Exception as e:
            logger.error(f"Database error: {e}")
            self.db.rollback()
            return 0

    def _print_summary(self):
        """Print collection summary."""
        logger.info("\n" + "=" * 60)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total items collected: {self.results['total_collected']}")
        logger.info("\nBy source:")
        for source, count in self.results['by_source'].items():
            logger.info(f"  {source}: {count} items")

        if self.results['errors']:
            logger.info(f"\nErrors encountered: {len(self.results['errors'])}")
            for error in self.results['errors']:
                logger.error(f"  - {error}")
        else:
            logger.info("\nNo errors!")

        logger.info("=" * 60)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run data collectors for Confluence Hub'
    )
    parser.add_argument(
        '--sources',
        nargs='+',
        choices=['42macro', 'youtube', 'substack', 'twitter', 'all'],
        default=['all'],
        help='Which sources to collect from (default: all)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Collect but do not save to database'
    )

    args = parser.parse_args()

    # Determine which sources to run
    if 'all' in args.sources:
        sources = ['42macro', 'youtube', 'substack', 'twitter']
    else:
        sources = args.sources

    logger.info(f"Running collectors: {', '.join(sources)}")

    # Create orchestrator
    orchestrator = CollectorOrchestrator()

    # Run collectors
    results = await orchestrator.run_all_collectors(sources)

    # Exit with error code if any errors
    if results['errors']:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    # Ensure logs directory exists
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)

    # Run orchestrator
    asyncio.run(main())
