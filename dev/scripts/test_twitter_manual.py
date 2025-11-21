"""
Manual Twitter Collection Test

Run the Twitter collector manually to fetch tweets and save to database.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.twitter_api import TwitterCollector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_twitter_collection():
    """Test Twitter collection manually."""

    print("=" * 80)
    print("MANUAL TWITTER COLLECTION TEST")
    print("=" * 80)

    # Get bearer token
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

    if not bearer_token:
        print("[ERROR] TWITTER_BEARER_TOKEN not found in .env file")
        print("\nTo get a bearer token:")
        print("1. Go to https://developer.twitter.com/en/portal/dashboard")
        print("2. Create a Free tier app")
        print("3. Go to Keys and Tokens")
        print("4. Copy the Bearer Token")
        print("5. Add to .env: TWITTER_BEARER_TOKEN=your_token_here")
        return

    print(f"[OK] Bearer token found: {bearer_token[:20]}...")
    print()

    # Initialize collector
    print("Initializing Twitter collector...")
    collector = TwitterCollector(bearer_token=bearer_token)
    print(f"[OK] Monitoring account: @MelMattison1")
    print()

    # Run full collection (collect + save to database)
    print("Running collection (this will save to database)...")
    print("-" * 80)

    result = await collector.run()

    print("-" * 80)
    print()
    print("RESULTS:")
    print(f"  Status: {result['status']}")
    print(f"  Collected: {result['collected']} items")
    print(f"  Saved to database: {result['saved']} items")
    print(f"  Time: {result['elapsed_seconds']}s")

    if result['status'] == 'error':
        print(f"\n[ERROR] Error: {result.get('error', 'Unknown error')}")
    elif result['saved'] == 0:
        print("\n[WARNING] No new tweets collected. This could mean:")
        print("  - @MelMattison1 hasn't posted since last collection")
        print("  - Rate limit reached (100 tweets/month on Free tier)")
        print("  - Account is private or unavailable")
    else:
        print(f"\n[SUCCESS] Successfully collected and saved {result['saved']} tweets!")
        print("\nCheck your database or dashboard to see the content.")

    print()
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_twitter_collection())
