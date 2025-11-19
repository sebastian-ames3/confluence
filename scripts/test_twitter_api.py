"""
Test script for Twitter API collector.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.twitter_api import TwitterCollector

# Load environment variables
load_dotenv(project_root / '.env')


async def main():
    """Test Twitter API collector."""

    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

    if not bearer_token:
        print("="*60)
        print("ERROR: TWITTER_BEARER_TOKEN not found in .env")
        print("="*60)
        print("\nTo get your Bearer Token:")
        print("1. Go to: https://developer.twitter.com/en/portal/dashboard")
        print("2. Sign in with your Twitter account")
        print("3. Create a new app (Free tier)")
        print("4. Go to 'Keys and Tokens' tab")
        print("5. Generate/Copy your Bearer Token")
        print("6. Add to .env: TWITTER_BEARER_TOKEN=your_token_here")
        print("\nFree tier limits: 1,500 tweets/month")
        print("="*60)
        sys.exit(1)

    print("="*60)
    print("TESTING TWITTER API COLLECTOR")
    print("="*60)

    # Initialize collector
    try:
        collector = TwitterCollector(bearer_token)
        print(f"\nAccounts configured: {len(collector.account_usernames)}")
        for username in collector.account_usernames:
            print(f"  - @{username}")
    except Exception as e:
        print(f"\nERROR initializing collector: {e}")
        sys.exit(1)

    # Collect tweets
    print("\n" + "-"*60)
    print("Collecting tweets...")
    print("-"*60)

    try:
        tweets = await collector.collect()

        print(f"\nSUCCESS! Collected {len(tweets)} tweets\n")

        if len(tweets) == 0:
            print("No tweets collected.")
            print("\nPossible reasons:")
            print("  - Accounts haven't tweeted recently")
            print("  - Accounts are private")
            print("  - API rate limit reached")
        else:
            # Show first 3 tweets as examples
            for i, tweet in enumerate(tweets[:3]):
                print(f"\nTweet {i+1}:")
                print(f"  Username: @{tweet['metadata']['username']}")
                print(f"  Created: {tweet['metadata']['created_at']}")
                print(f"  Likes: {tweet['metadata']['like_count']}")
                print(f"  Retweets: {tweet['metadata']['retweet_count']}")
                print(f"  Text: {tweet['content_text'][:150]}...")
                if tweet['metadata']['has_urls']:
                    print(f"  URLs: {', '.join(tweet['metadata']['urls'])}")

            if len(tweets) > 3:
                print(f"\n... and {len(tweets) - 3} more tweets")

            print("\n" + "="*60)
            print("Summary by account:")
            print("="*60)

            account_counts = {}
            for tweet in tweets:
                username = tweet['metadata']['username']
                account_counts[username] = account_counts.get(username, 0) + 1

            for username, count in account_counts.items():
                print(f"  @{username}: {count} tweets")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "="*60)
    print("Twitter API collector test PASSED!")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
