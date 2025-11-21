"""
Scheduled Tasks

Background scheduler for automated data collection (6am, 6pm daily).
Runs: YouTube, Substack, 42 Macro, KT Technical
Excluded: Discord (runs locally), Twitter (rate limits - manual only)
"""

import schedule
import time
import logging
from datetime import datetime
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.youtube_api import YouTubeCollector
from collectors.substack_rss import SubstackCollector
# from collectors.twitter_api import TwitterCollector  # Excluded - manual collection only
from collectors.macro42_selenium import Macro42Collector
from collectors.kt_technical import KTTechnicalCollector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def run_collection(time_label: str):
    """
    Run all collectors (except Discord).

    Args:
        time_label: "6am" or "6pm" for logging
    """
    logger.info(f"=" * 80)
    logger.info(f"Starting {time_label} collection run")
    logger.info(f"=" * 80)

    # Initialize collectors with credentials from environment
    collectors = []

    # YouTube
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    if youtube_api_key:
        collectors.append(("YouTube", YouTubeCollector(api_key=youtube_api_key)))
    else:
        logger.warning("[YouTube] Skipping - YOUTUBE_API_KEY not set")

    # Substack
    collectors.append(("Substack", SubstackCollector()))

    # Twitter - EXCLUDED from automated collection due to Free tier rate limits (100 API calls/month)
    # Twitter collector preserved for future manual use via chat interface or selective analysis
    # See: scripts/test_twitter_manual.py for manual collection
    # twitter_bearer = os.getenv('TWITTER_BEARER_TOKEN')
    # if twitter_bearer:
    #     collectors.append(("Twitter", TwitterCollector(bearer_token=twitter_bearer)))
    # else:
    #     logger.warning("[Twitter] Skipping - TWITTER_BEARER_TOKEN not set")

    # 42 Macro (using Selenium)
    macro42_email = os.getenv('MACRO42_EMAIL')
    macro42_password = os.getenv('MACRO42_PASSWORD')
    if macro42_email and macro42_password:
        collectors.append(("42 Macro", Macro42Collector(email=macro42_email, password=macro42_password, headless=True)))
    else:
        logger.warning("[42 Macro] Skipping - MACRO42_EMAIL and MACRO42_PASSWORD not set")

    # KT Technical
    kt_email = os.getenv('KT_EMAIL')
    kt_password = os.getenv('KT_PASSWORD')
    if kt_email and kt_password:
        collectors.append(("KT Technical", KTTechnicalCollector(email=kt_email, password=kt_password)))
    else:
        logger.warning("[KT Technical] Skipping - KT_EMAIL and KT_PASSWORD not set")

    results = {
        "total": len(collectors),
        "successful": 0,
        "failed": 0,
        "errors": []
    }

    for name, collector in collectors:
        try:
            logger.info(f"[{name}] Starting collection...")

            # Run full collection process (collect + save to database)
            result = await collector.run()

            # Log results
            if result["status"] == "success":
                logger.info(
                    f"[{name}] Collection complete - "
                    f"{result['saved']}/{result['collected']} items saved to database"
                )
                results["successful"] += 1
            else:
                raise Exception(result.get("error", "Unknown error"))

        except Exception as e:
            logger.error(f"[{name}] Collection failed: {e}")
            results["failed"] += 1
            results["errors"].append({"collector": name, "error": str(e)})

    # Summary
    logger.info(f"=" * 80)
    logger.info(f"{time_label} collection complete")
    logger.info(f"Successful: {results['successful']}/{results['total']}")
    logger.info(f"Failed: {results['failed']}/{results['total']}")
    if results["errors"]:
        logger.error(f"Errors encountered:")
        for error in results["errors"]:
            logger.error(f"  - {error['collector']}: {error['error']}")
    logger.info(f"=" * 80)

    return results


def collect_6am():
    """Morning collection routine - all collectors."""
    asyncio.run(run_collection("6am"))


def collect_6pm():
    """Evening collection routine - all collectors."""
    asyncio.run(run_collection("6pm"))


def run_manual_collection():
    """Manually trigger collection (for testing or on-demand)."""
    logger.info("Running manual collection...")
    return asyncio.run(run_collection("manual"))


def run_scheduler():
    """Main scheduler loop."""
    logger.info("=" * 80)
    logger.info("Macro Confluence Hub - Scheduler Started")
    logger.info("=" * 80)
    logger.info("Scheduled collections:")
    logger.info("  - 6:00 AM daily (YouTube, Substack, 42 Macro, KT Technical)")
    logger.info("  - 6:00 PM daily (YouTube, Substack, 42 Macro, KT Technical)")
    logger.info("")
    logger.info("Excluded collectors:")
    logger.info("  - Discord: Runs locally on Sebastian's laptop")
    logger.info("  - Twitter: Rate limits - manual collection only")
    logger.info("=" * 80)

    # Schedule daily tasks
    schedule.every().day.at("06:00").do(collect_6am)
    schedule.every().day.at("18:00").do(collect_6pm)

    # Main loop
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)  # Wait before retrying


if __name__ == "__main__":
    # Check if running as manual trigger
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        run_manual_collection()
    else:
        run_scheduler()
