#!/usr/bin/env python
"""
42 Macro Local Collection Script

Runs 42macro collector locally using Selenium and uploads to Railway API.
For use with Task Scheduler or manual execution.

Usage:
    python macro42_local.py --railway-api    # Upload to Railway (default)
    python macro42_local.py --local-db       # Save to local database
    python macro42_local.py --dry-run        # Test without saving
    python macro42_local.py --headful        # Show browser window (for debugging)
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
        logging.FileHandler(project_root / "logs" / "macro42_collection.log")
    ]
)
logger = logging.getLogger(__name__)


async def upload_to_railway(collected_data: list, source: str = "42macro") -> bool:
    """Upload collected data to Railway API."""
    import aiohttp

    railway_url = os.getenv("RAILWAY_API_URL", "https://confluence-production-a32e.up.railway.app")
    auth_user = os.getenv("AUTH_USERNAME", "sames3")
    auth_pass = os.getenv("AUTH_PASSWORD", "Spotswood1")

    endpoint = f"{railway_url}/api/collect/{source}"

    try:
        auth = aiohttp.BasicAuth(auth_user, auth_pass)
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=collected_data, auth=auth) as response:
                if response.status == 200:
                    logger.info(f"Successfully uploaded {len(collected_data)} items to Railway")
                    return True
                else:
                    logger.error(f"Upload failed: {response.status} - {await response.text()}")
                    return False
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return False


async def run_collection(args):
    """Run the 42macro collection."""
    # Get credentials from environment
    email = os.getenv("MACRO42_EMAIL")
    password = os.getenv("MACRO42_PASSWORD")

    if not email or not password:
        logger.error("MACRO42_EMAIL and MACRO42_PASSWORD must be set in .env file")
        sys.exit(1)

    # Determine mode
    use_local_db = args.local_db and not args.railway_api
    headless = not args.headful

    logger.info("=" * 60)
    logger.info("Starting 42 Macro Collection")
    logger.info(f"Mode: {'Local DB' if use_local_db else 'Railway API'}")
    logger.info(f"Browser: {'Headless' if headless else 'Visible'}")
    if args.dry_run:
        logger.info("DRY RUN - No data will be saved")
    logger.info("=" * 60)

    # Import collector after path setup
    from collectors.macro42_selenium import Macro42Collector

    # Create collector
    collector = Macro42Collector(
        email=email,
        password=password,
        headless=headless
    )

    # Set dry_run mode if requested
    if args.dry_run:
        collector.dry_run = True

    try:
        # Collect data
        collected_items = await collector.collect()

        if not collected_items:
            logger.info("No new items collected")
            return {"status": "success", "collected": 0, "saved": 0}

        logger.info(f"Collected {len(collected_items)} items")

        # Save data
        if args.dry_run:
            logger.info(f"[DRY RUN] Would save {len(collected_items)} items")
            saved_count = len(collected_items)
        elif use_local_db:
            saved_count = await collector.save_to_database(collected_items)
        else:
            # Upload to Railway API
            success = await upload_to_railway(collected_items, "42macro")
            saved_count = len(collected_items) if success else 0

        return {
            "status": "success",
            "collected": len(collected_items),
            "saved": saved_count
        }

    except Exception as e:
        logger.exception(f"Collection failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "collected": 0,
            "saved": 0
        }


def main():
    parser = argparse.ArgumentParser(description="Run 42 Macro collection locally")
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
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Show browser window (disable headless mode for debugging)"
    )
    args = parser.parse_args()

    # Ensure logs directory exists
    (project_root / "logs").mkdir(exist_ok=True)

    # Run collection
    result = asyncio.run(run_collection(args))

    logger.info("=" * 60)
    logger.info(f"Collection Result: {result['status']}")
    logger.info(f"Collected: {result.get('collected', 0)} items")
    logger.info(f"Saved: {result.get('saved', 0)} items")
    logger.info("=" * 60)

    if result["status"] == "error":
        logger.error(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
