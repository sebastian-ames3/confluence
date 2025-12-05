"""
Test script for YouTube collector.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.youtube_api import YouTubeCollector

# Load environment variables
load_dotenv(project_root / '.env')


async def main():
    """Test YouTube collector."""

    api_key = os.getenv('YOUTUBE_API_KEY')

    if not api_key:
        print("Error: YOUTUBE_API_KEY not found in .env")
        sys.exit(1)

    print("="*60)
    print("TESTING YOUTUBE COLLECTOR")
    print("="*60)

    # Initialize collector
    collector = YouTubeCollector(api_key)

    print(f"\nChannels configured: {len(collector.channels)}")
    for name, channel_id in collector.channels.items():
        print(f"  - {name}: {channel_id}")

    # Collect videos
    print("\n" + "-"*60)
    print("Collecting videos...")
    print("-"*60)

    try:
        videos = await collector.collect()

        print(f"\nSUCCESS! Collected {len(videos)} videos\n")

        # Show first 3 videos as examples
        for i, video in enumerate(videos[:3]):
            print(f"\nVideo {i+1}:")
            print(f"  Channel: {video['metadata']['channel_name']}")
            print(f"  Title: {video['metadata']['title']}")
            print(f"  URL: {video['url']}")
            print(f"  Published: {video['metadata']['published_at']}")
            print(f"  Duration: {video['metadata'].get('duration', 'N/A')}")
            print(f"  Views: {video['metadata'].get('view_count', 'N/A')}")
            print(f"  Transcript available: {video['metadata'].get('transcript_available', False)}")

        if len(videos) > 3:
            print(f"\n... and {len(videos) - 3} more videos")

        print("\n" + "="*60)
        print("Summary by channel:")
        print("="*60)

        channel_counts = {}
        for video in videos:
            channel = video['metadata']['channel_name']
            channel_counts[channel] = channel_counts.get(channel, 0) + 1

        for channel, count in channel_counts.items():
            print(f"  {channel}: {count} videos")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "="*60)
    print("YouTube collector test PASSED!")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
