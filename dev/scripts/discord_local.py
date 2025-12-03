"""
Discord Local Collection Script

Runs on Sebastian's laptop to collect Discord content using his logged-in session.
Scheduled to run twice daily (6am, 6pm) via Windows Task Scheduler.
Can save to local database or upload to Railway API.

Usage:
    python scripts/discord_local.py [--local-db | --railway-api]

Environment Variables Required:
    DISCORD_USER_TOKEN - Your Discord user token
"""

import asyncio
import json
import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path (dev/scripts -> dev -> project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from collectors.discord_self import DiscordSelfCollector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/discord_collection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def run_collection(use_local_db: bool = True):
    """
    Run Discord collection.

    Args:
        use_local_db: If True, save to local database. If False, upload to Railway API.
    """
    print("\n" + "="*70)
    print(f"Discord Collection - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")

    # Get Discord token from environment
    user_token = os.getenv("DISCORD_USER_TOKEN")

    if not user_token:
        logger.error("❌ DISCORD_USER_TOKEN not found in environment")
        print("\n⚠️  ERROR: DISCORD_USER_TOKEN not set!")
        print("\nPlease add your Discord user token to the .env file:")
        print("  DISCORD_USER_TOKEN=your_token_here")
        print("\nTo get your token:")
        print("  1. Open Discord in browser")
        print("  2. Press F12 -> Network tab")
        print("  3. Reload page")
        print("  4. Find any request to 'discord.com/api'")
        print("  5. Look for 'Authorization' header")
        print()
        return {"status": "error", "error": "Missing DISCORD_USER_TOKEN"}

    # Check if config file exists
    config_path = "config/discord_channels.json"
    if not Path(config_path).exists():
        logger.error(f"❌ Config file not found: {config_path}")
        print(f"\n⚠️  ERROR: {config_path} not found!")
        print("\nPlease:")
        print(f"  1. Copy config/discord_channels.json.template to {config_path}")
        print("  2. Run: python scripts/get_discord_channel_ids.py")
        print("  3. Fill in the channel IDs")
        print()
        return {"status": "error", "error": "Missing config file"}

    # Initialize collector
    try:
        collector = DiscordSelfCollector(
            user_token=user_token,
            config_path=config_path,
            use_local_db=use_local_db
        )
    except Exception as e:
        logger.error(f"❌ Failed to initialize collector: {e}")
        print(f"\n❌ Error: {e}\n")
        return {"status": "error", "error": str(e)}

    # Run collection
    try:
        logger.info("Starting collection...")
        result = await collector.run()

        # Print summary
        print(f"\n{'='*70}")
        print("Collection Summary")
        print(f"{'='*70}")
        print(f"Status: {result['status']}")
        print(f"Messages collected: {result['collected']}")
        print(f"Messages saved: {result['saved']}")
        print(f"Time elapsed: {result['elapsed_seconds']}s")
        print(f"Timestamp: {result['timestamp']}")

        if result['status'] == 'error':
            print(f"Error: {result.get('error', 'Unknown error')}")

        print(f"{'='*70}\n")

        # Save backup if upload failed
        if not use_local_db and result['status'] != 'success':
            backup_file = f"discord_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(result, f, indent=2)
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
        description="Discord content collector for Macro Confluence Hub"
    )
    parser.add_argument(
        '--local-db',
        action='store_true',
        help='Save to local database (default)'
    )
    parser.add_argument(
        '--railway-api',
        action='store_true',
        help='Upload to Railway API instead of local database'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test collection without saving (prints results only)'
    )

    args = parser.parse_args()

    # Determine mode
    if args.railway_api:
        use_local_db = False
        logger.info("Mode: Railway API upload")
    else:
        use_local_db = True
        logger.info("Mode: Local database")

    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Run collection
    try:
        result = asyncio.run(run_collection(use_local_db=use_local_db))

        # Exit with appropriate code
        if result["status"] == "success":
            sys.exit(0)
        elif result["status"] == "cancelled":
            sys.exit(130)  # Standard exit code for Ctrl+C
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n👋 Cancelled.\n")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
