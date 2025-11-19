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

    # Collect tweets/threads
    print("\n" + "-"*60)
    print("Collecting tweets/threads...")
    print("Requesting: 5 items (threads count as 1)")
    print("-"*60)

    try:
        result = await collector.collect(num_items=5, download_media=True)

        tweets = result["content"]
        quota_used = result["quota_used"]
        media_downloaded = result["media_downloaded"]

        print(f"\nSUCCESS! Collected {len(tweets)} items\n")
        print(f"API calls made: {quota_used}")
        print(f"Media downloaded: {media_downloaded['images']} images, {media_downloaded['videos']} videos\n")

        if len(tweets) == 0:
            print("No tweets collected.")
            print("\nPossible reasons:")
            print("  - Accounts haven't tweeted recently")
            print("  - Accounts are private")
            print("  - API rate limit reached")
        else:
            # Show first 3 items as examples
            for i, item in enumerate(tweets[:3]):
                is_thread = item['metadata'].get('is_thread', False)
                thread_len = item['metadata'].get('thread_length', 1)

                print(f"\nItem {i+1} {'[THREAD]' if is_thread else '[TWEET]'}:")
                print(f"  Username: @{item['metadata']['username']}")
                print(f"  Type: {item['content_type']}")
                if is_thread:
                    print(f"  Thread length: {thread_len} tweets")
                print(f"  Created: {item['metadata']['created_at']}")
                print(f"  Likes: {item['metadata']['public_metrics']['like_count']}")
                print(f"  Retweets: {item['metadata']['public_metrics']['retweet_count']}")
                print(f"  Media: {item['metadata']['media_count']} files")
                if item['metadata']['media_count'] > 0:
                    media_types = [m['type'] for m in item['metadata']['media']]
                    print(f"  Media types: {', '.join(media_types)}")
                if item['metadata'].get('quoted_tweet'):
                    print(f"  Quote tweet: {item['metadata']['quoted_tweet']['url']}")
                print(f"  Text preview: {item['content_text'][:150]}...")

            if len(tweets) > 3:
                print(f"\n... and {len(tweets) - 3} more tweets")

            print("\n" + "="*60)
            print("Summary:")
            print("="*60)

            # Count threads vs tweets
            thread_count = sum(1 for t in tweets if t['metadata'].get('is_thread', False))
            tweet_count = len(tweets) - thread_count

            print(f"  Threads: {thread_count}")
            print(f"  Single tweets: {tweet_count}")
            print(f"  Total items: {len(tweets)}")
            print(f"\n  API quota used: {quota_used}")
            print(f"  Images downloaded: {media_downloaded['images']}")
            print(f"  Videos downloaded: {media_downloaded['videos']}")

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
