"""
Test script for 42 Macro Selenium collector.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collectors.macro42_selenium import Macro42Collector

# Load environment variables
load_dotenv(project_root / '.env')


async def main():
    """Test 42 Macro Selenium collector."""

    email = os.getenv('MACRO42_EMAIL')
    password = os.getenv('MACRO42_PASSWORD')

    if not email or not password:
        print("="*60)
        print("ERROR: MACRO42_EMAIL and MACRO42_PASSWORD not found in .env")
        print("="*60)
        sys.exit(1)

    print("="*60)
    print("TESTING 42 MACRO SELENIUM COLLECTOR")
    print("="*60)
    print(f"\nEmail: {email}")
    print(f"Password: {'*' * len(password)}")
    print("\nNote: Using Selenium with headless Chrome")
    print("This may take 10-20 seconds...")

    # Initialize collector (headless=False to see browser)
    collector = Macro42Collector(email, password, headless=True)

    # Collect content
    print("\n" + "-"*60)
    print("Collecting content...")
    print("-"*60)

    try:
        items = await collector.collect()

        print(f"\nSUCCESS! Collected {len(items)} items\n")

        if len(items) == 0:
            print("No items collected.")
            print("\nPossible reasons:")
            print("  1. Login selectors need customization (site HTML changed)")
            print("  2. PDF/video selectors need customization")
            print("  3. Account locked or requires 2FA")
            print("\nNext steps:")
            print("  - Run with headless=False to see browser")
            print("  - Update selectors in collectors/macro42_selenium.py")
        else:
            # Show items
            pdf_count = sum(1 for item in items if item['content_type'] == 'pdf')
            video_count = sum(1 for item in items if item['content_type'] == 'video')

            print(f"PDFs: {pdf_count}")
            print(f"Videos: {video_count}")

            # Show first 3 items
            for i, item in enumerate(items[:3]):
                print(f"\nItem {i+1}:")
                print(f"  Type: {item['content_type']}")
                print(f"  Title: {item.get('content_text', 'N/A')[:100]}")
                print(f"  URL: {item.get('url', 'N/A')[:80]}...")
                if item.get('file_path'):
                    print(f"  Downloaded: {item['file_path']}")

            if len(items) > 3:
                print(f"\n... and {len(items) - 3} more items")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*60)
        print("Troubleshooting:")
        print("="*60)
        print("1. Check if Chrome is installed")
        print("2. Verify 42 Macro credentials in .env")
        print("3. Run with headless=False to see what's happening")
        print("4. Check if 42 Macro login page HTML changed")
        sys.exit(1)

    print("\n" + "="*60)
    print("42 Macro Selenium collector test PASSED!")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
