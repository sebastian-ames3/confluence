"""
Test script for Substack collector.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.substack_rss import SubstackCollector


async def main():
    """Test Substack collector."""

    print("="*60)
    print("TESTING SUBSTACK COLLECTOR")
    print("="*60)

    # Initialize collector (uses default Visser Labs)
    collector = SubstackCollector()

    print(f"\nSubstack feeds configured: {len(collector.substack_urls)}")
    for url in collector.substack_urls:
        print(f"  - {url}")

    # Collect articles
    print("\n" + "-"*60)
    print("Collecting articles...")
    print("-"*60)

    try:
        articles = await collector.collect()

        print(f"\nSUCCESS! Collected {len(articles)} articles\n")

        # Show first 3 articles as examples
        for i, article in enumerate(articles[:3]):
            print(f"\nArticle {i+1}:")
            print(f"  Author: {article['metadata']['author']}")
            print(f"  Title: {article['metadata']['title']}")
            print(f"  URL: {article['url']}")
            print(f"  Published: {article['metadata']['published_at']}")
            print(f"  Word count: {article['metadata']['word_count']}")
            print(f"  Has images: {article['metadata']['has_images']}")
            print(f"  Preview: {article['content_text'][:150]}...")

        if len(articles) > 3:
            print(f"\n... and {len(articles) - 3} more articles")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "="*60)
    print("Substack collector test PASSED!")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
