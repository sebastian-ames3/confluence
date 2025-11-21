"""
Test script for Transcript Harvester Agent.

Tests the full pipeline: video download -> audio extraction -> transcription -> analysis
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.transcript_harvester import TranscriptHarvesterAgent

# Load environment variables
load_dotenv(project_root / '.env')


async def main():
    """Test Transcript Harvester Agent."""

    claude_api_key = os.getenv('CLAUDE_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY') or os.getenv('WHISPER_API_KEY')

    if not claude_api_key:
        print("Error: CLAUDE_API_KEY not found in .env")
        sys.exit(1)

    if not openai_api_key:
        print("Error: OPENAI_API_KEY or WHISPER_API_KEY not found in .env")
        sys.exit(1)

    print("="*60)
    print("TESTING TRANSCRIPT HARVESTER AGENT")
    print("="*60)

    # Initialize agent
    print("\nInitializing Transcript Harvester Agent...")
    agent = TranscriptHarvesterAgent(
        claude_api_key=claude_api_key,
        openai_api_key=openai_api_key
    )
    print(f"Downloads directory: {agent.downloads_dir}")

    # Test video (short public YouTube video for testing)
    # Using a short financial news video (replace with actual test video)
    test_video_url = input("\nEnter YouTube video URL to test (or press Enter for default): ").strip()

    if not test_video_url:
        # Default: Use a short public market analysis video
        print("\nUsing default test video...")
        test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with actual short financial video
        print(f"Note: Replace this URL with a real short market analysis video")
        print("For now, enter a valid YouTube URL when prompted.\n")
        return

    print(f"\nTest video: {test_video_url}")

    # Get priority tier
    print("\nPriority tiers:")
    print("  1 = HIGH (Imran Discord, Darius 42 Macro)")
    print("  2 = MEDIUM (Mel Twitter)")
    print("  3 = STANDARD (YouTube long-form)")

    priority_choice = input("Select priority tier (1/2/3) [default=2]: ").strip() or "2"
    priority_map = {"1": "high", "2": "medium", "3": "standard"}
    priority = priority_map.get(priority_choice, "medium")

    # Run harvest
    print("\n" + "-"*60)
    print("Running full harvest pipeline...")
    print("-"*60)
    print("\nStep 1: Downloading video and extracting audio...")
    print("Step 2: Transcribing with Whisper API...")
    print("Step 3: Analyzing transcript with Claude...")
    print("\nThis may take several minutes for longer videos.\n")

    try:
        result = await agent.harvest(
            video_url=test_video_url,
            source="test_youtube",
            metadata={
                "speaker": "Test Speaker",
                "title": "Market Analysis Test",
                "date": "2025-11-19"
            },
            priority=priority
        )

        print("\n" + "="*60)
        print("SUCCESS! Transcript harvested and analyzed")
        print("="*60)

        # Display results
        print(f"\nVideo URL: {result['video_url']}")
        print(f"Source: {result['source']}")
        print(f"Priority: {result['priority']}")
        print(f"Processed at: {result['processed_at']}")

        print(f"\n--- ANALYSIS RESULTS ---")
        print(f"\nSentiment: {result['sentiment']}")
        print(f"Conviction: {result['conviction']}/10")
        print(f"Time Horizon: {result['time_horizon']}")

        print(f"\nKey Themes ({len(result['key_themes'])}):")
        for i, theme in enumerate(result['key_themes'], 1):
            print(f"  {i}. {theme}")

        if result['tickers_mentioned']:
            print(f"\nTickers Mentioned ({len(result['tickers_mentioned'])}):")
            print(f"  {', '.join(result['tickers_mentioned'])}")

        if result.get('catalysts'):
            print(f"\nCatalysts ({len(result['catalysts'])}):")
            for i, catalyst in enumerate(result['catalysts'], 1):
                print(f"  {i}. {catalyst}")

        if result.get('falsification_criteria'):
            print(f"\nFalsification Criteria ({len(result['falsification_criteria'])}):")
            for i, criterion in enumerate(result['falsification_criteria'], 1):
                print(f"  {i}. {criterion}")

        if result.get('key_quotes'):
            print(f"\nKey Quotes ({len(result['key_quotes'])}):")
            for i, quote in enumerate(result['key_quotes'], 1):
                print(f"  {i}. [{quote.get('timestamp', 'N/A')}] {quote.get('text', '')[:100]}...")

        print(f"\nTranscript length: {len(result['transcript'])} characters")
        print(f"Video duration: {result.get('video_duration_seconds', 'N/A')} seconds")

        # Option to save full results
        save_choice = input("\nSave full results to JSON file? (y/n): ").strip().lower()
        if save_choice == 'y':
            output_file = project_root / "debug" / "transcript_harvest_test.json"
            output_file.parent.mkdir(exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"Results saved to: {output_file}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "="*60)
    print("Transcript Harvester test PASSED!")
    print("="*60)


if __name__ == '__main__':
    asyncio.run(main())
