"""
42 Macro Local Collection Script

Runs on Sebastian's laptop to collect 42 Macro content using Selenium.
Scheduled to run daily via Windows Task Scheduler.
Uploads collected content to Railway API.

Usage:
    python dev/scripts/macro42_local.py [--local-db | --railway-api]

Environment Variables Required:
    MACRO42_EMAIL - Your 42macro account email
    MACRO42_PASSWORD - Your 42macro account password
    RAILWAY_API_URL - Railway API URL (for --railway-api mode)
"""

import asyncio
import json
import os
import sys
import argparse
import logging
import aiohttp
from datetime import datetime
from pathlib import Path

# Add project root to path (dev/scripts -> dev -> project root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables BEFORE importing collectors
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from collectors.macro42_selenium import Macro42Collector

# Configure logging
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'macro42_collection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def get_railway_api_url() -> str:
    """Get Railway API URL from environment."""
    url = os.getenv("RAILWAY_API_URL", "https://confluence-production-a32e.up.railway.app")
    return url.rstrip("/")


async def upload_to_railway(collected_data: list) -> bool:
    """
    Upload collected data to Railway API.

    Args:
        collected_data: List of collected content items

    Returns:
        True if upload successful
    """
    if not collected_data:
        logger.info("No data to upload")
        return True

    railway_url = f"{get_railway_api_url()}/api/collect/42macro"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(railway_url, json=collected_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"[SUCCESS] Uploaded to Railway: {result}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"[FAILED] Upload failed: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.error(f"[ERROR] Upload error: {e}")
        return False


async def run_collection(use_local_db: bool = False):
    """
    Run 42 Macro collection.

    Args:
        use_local_db: If True, save to local database. If False, upload to Railway API.
    """
    print("\n" + "="*70)
    print(f"42 Macro Collection - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    # Get credentials from environment
    email = os.getenv("MACRO42_EMAIL")
    password = os.getenv("MACRO42_PASSWORD")

    if not email or not password:
        logger.error("❌ MACRO42_EMAIL or MACRO42_PASSWORD not found in environment")
        print("\n⚠️  ERROR: 42macro credentials not set!")
        print("\nPlease add to your .env file:")
        print("  MACRO42_EMAIL=your_email@example.com")
        print("  MACRO42_PASSWORD=your_password")
        print()
        return {"status": "error", "error": "Missing credentials"}

    # Initialize collector
    try:
        collector = Macro42Collector(
            email=email,
            password=password,
            headless=True  # Run headless for scheduled tasks
        )
    except Exception as e:
        logger.error(f"❌ Failed to initialize collector: {e}")
        print(f"\n❌ Error: {e}\n")
        return {"status": "error", "error": str(e)}

    # Run collection
    start_time = datetime.now()
    try:
        logger.info("Starting 42 Macro collection...")
        collected_items = await collector.collect()

        elapsed_time = (datetime.now() - start_time).total_seconds()

        # Upload to Railway or save locally
        if collected_items:
            if use_local_db:
                # Save to local database (not implemented yet)
                logger.info("Local DB mode not implemented - would save locally")
                saved_count = len(collected_items)
                upload_success = True
            else:
                # Upload to Railway API
                upload_success = await upload_to_railway(collected_items)
                saved_count = len(collected_items) if upload_success else 0
        else:
            saved_count = 0
            upload_success = True

        result = {
            "status": "success" if upload_success else "partial",
            "source": "42macro",
            "collected": len(collected_items),
            "saved": saved_count,
            "elapsed_seconds": round(elapsed_time, 2),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Print summary
        print(f"\n{'='*70}")
        print("Collection Summary")
        print(f"{'='*70}")
        print(f"Status: {result['status']}")
        print(f"PDFs collected: {len([i for i in collected_items if i.get('content_type') == 'pdf'])}")
        print(f"Videos collected: {len([i for i in collected_items if i.get('content_type') == 'video'])}")
        print(f"Total collected: {result['collected']}")
        print(f"Items saved: {result['saved']}")
        print(f"Time elapsed: {result['elapsed_seconds']}s")
        print(f"Timestamp: {result['timestamp']}")
        print(f"{'='*70}\n")

        # Save backup if upload failed
        if not use_local_db and not upload_success:
            backup_file = project_root / f"macro42_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(collected_items, f, indent=2)
            logger.warning(f"💾 Backup saved to {backup_file}")
            print(f"💾 Backup saved to {backup_file}\n")

        return result

    except KeyboardInterrupt:
        logger.info("Collection cancelled by user")
        print("\n\n👋 Cancelled by user.\n")
        return {"status": "cancelled"}

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        print(f"\n❌ Collection failed: {e}\n")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="42 Macro content collector for Macro Confluence Hub"
    )
    parser.add_argument(
        '--local-db',
        action='store_true',
        help='Save to local database'
    )
    parser.add_argument(
        '--railway-api',
        action='store_true',
        help='Upload to Railway API (default)'
    )

    args = parser.parse_args()

    # Default to Railway API if neither specified
    use_local_db = args.local_db and not args.railway_api

    if use_local_db:
        print("Mode: Local Database")
    else:
        print(f"Mode: Railway API ({get_railway_api_url()})")

    # Run the async collection
    result = asyncio.run(run_collection(use_local_db=use_local_db))

    # Exit with appropriate code
    if result.get("status") == "success":
        sys.exit(0)
    elif result.get("status") == "cancelled":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
