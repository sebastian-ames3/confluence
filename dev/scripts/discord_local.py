#!/usr/bin/env python
"""
Discord Local Collection Script

Runs Discord collector locally and uploads to Railway API.
For use with Task Scheduler or manual execution.

Usage:
    python discord_local.py --railway-api    # Upload to Railway (default)
    python discord_local.py --local-db       # Save to local database
    python discord_local.py --dry-run        # Test without saving
"""

import asyncio
import argparse
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / "logs" / "discord_collection.log")
    ]
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Run Discord collection locally")
    parser.add_argument(
        "--railway-api",
        action="store_true",
        default=True,
        help="Upload collected data to Railway API (default)"
    )
    parser.add_argument(
        "--local-db",
        action="store_true",
        help="Save to local database instead of Railway"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test collection without saving data"
    )
    args = parser.parse_args()

    # Ensure logs directory exists
    (project_root / "logs").mkdir(exist_ok=True)

    # Get Discord token from environment
    discord_token = os.getenv("DISCORD_USER_TOKEN")
    if not discord_token:
        logger.error("DISCORD_USER_TOKEN not found in .env file")
        sys.exit(1)

    # Determine mode
    use_local_db = args.local_db and not args.railway_api

    logger.info("=" * 60)
    logger.info("Starting Discord Collection")
    logger.info(f"Mode: {'Local DB' if use_local_db else 'Railway API'}")
    if args.dry_run:
        logger.info("DRY RUN - No data will be saved")
    logger.info("=" * 60)

    # Import collector after path setup
    from collectors.discord_self import DiscordSelfCollector

    # Create collector
    collector = DiscordSelfCollector(
        user_token=discord_token,
        config_path=str(project_root / "config" / "discord_channels.json"),
        use_local_db=use_local_db
    )

    # Set dry_run mode if requested
    if args.dry_run:
        collector.dry_run = True

    # Run collection
    try:
        result = asyncio.run(collector.run())

        logger.info("=" * 60)
        logger.info(f"Collection Result: {result['status']}")
        logger.info(f"Collected: {result.get('collected', 0)} items")
        logger.info(f"Saved: {result.get('saved', 0)} items")
        logger.info(f"Elapsed: {result.get('elapsed_seconds', 0):.2f}s")
        logger.info("=" * 60)

        if result["status"] == "error":
            logger.error(f"Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Collection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
