"""
Simple script to get YouTube channel IDs from channel URLs.
Just paste the channel URL and it will extract the ID.
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


def get_channel_id_from_url(youtube, channel_url):
    """
    Get channel ID by fetching the channel page.

    For URLs like:
    - https://www.youtube.com/@peterdiamandis
    - https://www.youtube.com/channel/UCxxxxx
    """
    try:
        # Extract handle from URL
        if '@' in channel_url:
            handle = channel_url.split('@')[1].strip('/').split('/')[0]

            # Search for the exact channel name/handle
            search_response = youtube.search().list(
                part='snippet',
                q=f"@{handle}",
                type='channel',
                maxResults=1
            ).execute()

            if search_response.get('items'):
                return search_response['items'][0]['snippet']['channelId']

        elif '/channel/' in channel_url:
            # Already has the channel ID in the URL
            return channel_url.split('/channel/')[1].strip('/').split('/')[0]

        return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    api_key = os.getenv('YOUTUBE_API_KEY')

    if not api_key:
        print("Error: YOUTUBE_API_KEY not found")
        sys.exit(1)

    youtube = build('youtube', 'v3', developerKey=api_key)

    # Channel URLs
    channels = {
        "Peter Diamandis": "https://www.youtube.com/@peterdiamandis",
        "Jordi Visser": "https://www.youtube.com/@JordiVisserLabs",
        "42 Macro": "https://www.youtube.com/@42Macro",
        "Forward Guidance": "https://www.youtube.com/@ForwardGuidanceBW"
    }

    print("Getting YouTube Channel IDs...\n")

    results = {}
    for name, url in channels.items():
        print(f"Looking up {name}...")
        channel_id = get_channel_id_from_url(youtube, url)

        if channel_id:
            results[name] = channel_id
            print(f"  Found: {channel_id}\n")
        else:
            results[name] = None
            print(f"  Not found\n")

    # Print results
    print("="*60)
    print("RESULTS:")
    print("="*60)
    for name, channel_id in results.items():
        if channel_id:
            print(f"{name:<25} {channel_id}")
        else:
            print(f"{name:<25} NOT FOUND")

    print("\n" + "="*60)
    print("UPDATE collectors/youtube_api.py CHANNELS dict with:")
    print("="*60)
    print("CHANNELS = {")
    if results.get("Peter Diamandis"):
        print(f'    "peter_diamandis": "{results["Peter Diamandis"]}",')
    if results.get("Jordi Visser"):
        print(f'    "jordi_visser": "{results["Jordi Visser"]}",')
    if results.get("Forward Guidance"):
        print(f'    "forward_guidance": "{results["Forward Guidance"]}",')
    if results.get("42 Macro"):
        print(f'    "42macro": "{results["42 Macro"]}"')
    print("}")


if __name__ == '__main__':
    main()
