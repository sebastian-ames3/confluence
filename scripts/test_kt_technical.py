"""
Test script for KT Technical Analysis collector.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.kt_technical import KTTechnicalCollector

# Load environment variables
load_dotenv(project_root / '.env')


async def main():
    """Test KT Technical Analysis collector."""

    email = os.getenv('KT_EMAIL')
    password = os.getenv('KT_PASSWORD')

    if not email or not password:
        print("="*60)
        print("ERROR: KT_EMAIL and KT_PASSWORD not found in .env")
        print("="*60)
        print("\nAdd your KT Technical Analysis credentials to .env:")
        print("KT_EMAIL=your_email@example.com")
        print("KT_PASSWORD=your_password")
        print("="*60)
        sys.exit(1)

    print("="*60)
    print("TESTING KT TECHNICAL ANALYSIS COLLECTOR")
    print("="*60)
    print(f"\nEmail: {email}")
    print(f"Password: {'*' * len(password)}")

    # Initialize collector
    collector = KTTechnicalCollector(email, password)

    # Collect content
    print("\n" + "-"*60)
    print("Collecting blog posts...")
    print("-"*60)

    try:
        posts = await collector.collect()

        print(f"\nSUCCESS! Collected {len(posts)} blog posts\n")

        if len(posts) == 0:
            print("No posts collected.")
            print("\nPossible reasons:")
            print("  1. Login credentials incorrect")
            print("  2. HTML selectors need customization")
            print("  3. Website structure changed")
            print("\nNext steps:")
            print("  - Verify credentials on website manually")
            print("  - Check if blog feed page requires different URL")
            print("  - Update selectors in collectors/kt_technical.py")
        else:
            # Show posts
            for i, post in enumerate(posts):
                print(f"\nPost {i+1}:")
                print(f"  Title: {post['metadata']['title']}")
                print(f"  URL: {post['url']}")
                print(f"  Date: {post['metadata'].get('published_date', 'N/A')}")
                print(f"  Images: {post['metadata']['num_images']}")

                # Show content preview
                content_preview = post['content_text'][:200]
                print(f"  Preview: {content_preview}...")

                # Show downloaded images
                if post['metadata']['image_paths']:
                    print(f"  Downloaded images:")
                    for img_path in post['metadata']['image_paths'][:3]:
                        print(f"    - {img_path}")

            if len(posts) > 3:
                print(f"\n... and {len(posts) - 3} more posts")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*60)
        print("Troubleshooting:")
        print("="*60)
        print("1. Verify login credentials work on website")
        print("2. Check if website structure/URLs changed")
        print("3. Update HTML selectors if needed")
        print("4. Check network connectivity")
        sys.exit(1)

    print("\n" + "="*60)
    print("KT Technical Analysis collector test PASSED!")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
