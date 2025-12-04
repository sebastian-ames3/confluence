"""
PRD-018 Transcription Test

Quick test to verify the transcription pipeline works end-to-end.
Uses a short public YouTube video to test yt-dlp + Whisper API.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env')


async def test_transcription():
    """Test the transcription pipeline with a short video."""

    print("=" * 60)
    print("PRD-018 TRANSCRIPTION TEST")
    print("=" * 60)

    # Check environment
    print("\n1. Checking environment...")

    claude_key = os.getenv('CLAUDE_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY') or os.getenv('WHISPER_API_KEY')

    if not claude_key:
        print("   ERROR: CLAUDE_API_KEY not set")
        return False
    print(f"   CLAUDE_API_KEY: {claude_key[:20]}...")

    if not openai_key:
        print("   ERROR: OPENAI_API_KEY or WHISPER_API_KEY not set")
        return False
    print(f"   OPENAI_API_KEY: {openai_key[:20]}...")

    # Check yt-dlp
    print("\n2. Checking yt-dlp...")
    import subprocess
    result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
    if result.returncode != 0:
        print("   ERROR: yt-dlp not available")
        return False
    print(f"   yt-dlp version: {result.stdout.strip()}")

    # Check ffmpeg
    print("\n3. Checking ffmpeg...")
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
    if result.returncode != 0:
        print("   ERROR: ffmpeg not available")
        return False
    print(f"   ffmpeg available: YES")

    # Initialize agent
    print("\n4. Initializing TranscriptHarvesterAgent...")
    try:
        from agents.transcript_harvester import TranscriptHarvesterAgent
        agent = TranscriptHarvesterAgent()
        print(f"   Agent initialized successfully")
        print(f"   Downloads dir: {agent.downloads_dir}")
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

    # Test with a very short public video (10 seconds)
    # This is a Creative Commons test video
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video, 19 seconds

    print(f"\n5. Testing transcription with short video...")
    print(f"   URL: {test_url}")
    print(f"   This may take 1-2 minutes...")

    try:
        result = await agent.harvest(
            video_url=test_url,
            source="test",
            metadata={
                "title": "Test Video",
                "speaker": "Test"
            },
            priority="standard"
        )

        print(f"\n6. Results:")
        print(f"   Transcript length: {len(result.get('transcript', ''))} chars")
        print(f"   Duration: {result.get('video_duration_seconds', 'N/A')} seconds")
        print(f"   Sentiment: {result.get('sentiment', 'N/A')}")
        print(f"   Key themes: {result.get('key_themes', [])[:3]}")

        if result.get('transcript'):
            print(f"\n   Transcript preview:")
            print(f"   {result['transcript'][:200]}...")
            print("\n" + "=" * 60)
            print("SUCCESS: Transcription pipeline working!")
            print("=" * 60)
            return True
        else:
            print("   ERROR: No transcript returned")
            return False

    except Exception as e:
        print(f"\n   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = asyncio.run(test_transcription())
    sys.exit(0 if success else 1)
