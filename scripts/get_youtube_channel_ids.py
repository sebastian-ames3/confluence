"""
Helper script to get YouTube channel IDs from channel handles.

Requires YOUTUBE_API_KEY in .env file.
"""

import os
import sys
from pathlib import Path
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

# Channel handles to look up
CHANNEL_HANDLES = [
    "@peterdiamandis",
    "@JordiVisserLabs",
    "@42Macro",
    "@ForwardGuidanceBW"
]


def get_channel_id_from_handle(youtube, handle):
    """
    Get channel ID from a channel handle using YouTube Data API.

    Args:
        youtube: YouTube API client
        handle: Channel handle (e.g., "@peterdiamandis")

    Returns:
        Channel ID or None
    """
    try:
        # Remove @ if present
        username = handle.lstrip('@')

        # Try searching by handle/username
        search_response = youtube.search().list(
            part='snippet',
            q=handle,
            type='channel',
            maxResults=5
        ).execute()

        # Check if we got results
        for item in search_response.get('items', []):
            channel_title = item['snippet']['title'].lower()
            channel_id = item['snippet']['channelId']

            # Try to match the handle to the result
            # This is fuzzy matching - adjust as needed
            if username.lower().replace('@', '') in channel_title.replace(' ', '').lower():
                return channel_id

        # If search didn't work, try getting channel by custom URL
        # This requires trying the channel endpoint directly
        return None

    except Exception as e:
        print(f"Error looking up {handle}: {e}")
        return None


def main():
    """Main function to get all channel IDs."""

    # Get API key
    api_key = os.getenv('YOUTUBE_API_KEY')

    if not api_key:
        print("Error: YOUTUBE_API_KEY not found in .env file")
        print("Please add your YouTube Data API key to .env:")
        print("YOUTUBE_API_KEY=your_api_key_here")
        sys.exit(1)

    print("Looking up YouTube channel IDs...\n")

    # Build YouTube API client
    youtube = build('youtube', 'v3', developerKey=api_key)

    # Look up each channel
    results = {}
    for handle in CHANNEL_HANDLES:
        print(f"Looking up {handle}...")
        channel_id = get_channel_id_from_handle(youtube, handle)

        if channel_id:
            results[handle] = channel_id
            print(f"  Found: {channel_id}")
        else:
            print(f"  Not found (will try alternate method)")
            results[handle] = None

    # Print summary
    print("\n" + "="*60)
    print("CHANNEL IDs FOUND")
    print("="*60)

    for handle, channel_id in results.items():
        if channel_id:
            print(f"{handle:<25} {channel_id}")
        else:
            print(f"{handle:<25} NOT FOUND - try manual lookup")

    # Print code to update collectors/youtube_api.py
    print("\n" + "="*60)
    print("UPDATE collectors/youtube_api.py WITH:")
    print("="*60)
    print("CHANNELS = {")

    if results.get("@peterdiamandis"):
        print(f'    "peter_diamandis": "{results["@peterdiamandis"]}",')
    if results.get("@JordiVisserLabs"):
        print(f'    "jordi_visser": "{results["@JordiVisserLabs"]}",')
    if results.get("@ForwardGuidanceBW"):
        print(f'    "forward_guidance": "{results["@ForwardGuidanceBW"]}",')
    if results.get("@42Macro"):
        print(f'    "42macro": "{results["@42Macro"]}"')

    print("}")

    # Manual lookup instructions
    print("\n" + "="*60)
    print("MANUAL LOOKUP (if any not found):")
    print("="*60)
    print("1. Go to the channel page in your browser")
    print("2. Right-click → View Page Source")
    print("3. Search (Ctrl+F) for: \"channelId\"")
    print("4. Copy the ID that looks like: UCxxxxxxxxxxxxxxxxxxxxx")
    print("="*60)


if __name__ == '__main__':
    main()
