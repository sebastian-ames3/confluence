#!/usr/bin/env python
"""
42 Macro Local Collection Script

Runs 42macro collector locally using Selenium and uploads to Railway API.
Includes local transcription of videos using authenticated session.

Video Transcription Flow:
1. Selenium collects video URLs with authenticated session (cookies saved)
2. yt-dlp downloads videos locally using those cookies
3. Whisper API transcribes audio to text
4. Claude analyzes transcript for themes/sentiment
5. Transcript + analysis uploaded to Railway with video metadata
6. Local audio files cleaned up

Usage:
    python macro42_local.py --railway-api    # Upload to Railway (default)
    python macro42_local.py --local-db       # Save to local database
    python macro42_local.py --dry-run        # Test without saving
    python macro42_local.py --headful        # Show browser window (for debugging)
    python macro42_local.py --skip-transcription  # Skip video transcription
"""

import asyncio
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / "logs" / "macro42_collection.log")
    ]
)
logger = logging.getLogger(__name__)


async def transcribe_videos_locally(
    collected_items: List[Dict[str, Any]],
    dry_run: bool = False
) -> List[Dict[str, Any]]:
    """
    Transcribe video items locally using the authenticated session.

    Uses the cookies saved by Selenium to download private Vimeo videos,
    then transcribes with Whisper and analyzes with Claude.

    Args:
        collected_items: List of collected items (videos and PDFs)
        dry_run: If True, skip actual transcription

    Returns:
        Updated list with transcripts added to video items
    """
    from agents.transcript_harvester import TranscriptHarvesterAgent

    # Separate videos from other content
    videos = [item for item in collected_items if item.get("content_type") == "video"]
    other_items = [item for item in collected_items if item.get("content_type") != "video"]

    if not videos:
        logger.info("No videos to transcribe")
        return collected_items

    logger.info(f"Found {len(videos)} videos to transcribe locally")

    if dry_run:
        logger.info("[DRY RUN] Would transcribe videos locally")
        return collected_items

    # Initialize harvester
    try:
        harvester = TranscriptHarvesterAgent()
    except Exception as e:
        logger.error(f"Failed to initialize TranscriptHarvesterAgent: {e}")
        logger.warning("Skipping transcription - videos will be uploaded without transcripts")
        return collected_items

    transcribed_videos = []
    failed_count = 0

    for i, video in enumerate(videos):
        video_url = video.get("url")
        metadata = video.get("metadata", {})
        title = metadata.get("title", f"Video {i+1}")

        logger.info(f"[{i+1}/{len(videos)}] Transcribing: {title}")

        try:
            # Run the harvest pipeline (download -> transcribe -> analyze)
            result = await harvester.harvest(
                video_url=video_url,
                source="42macro",
                metadata=metadata,
                priority="high"  # 42macro is Tier 1
            )

            if result and result.get("transcript"):
                # Add transcript and analysis to the video item
                video["content_text"] = result["transcript"]
                video["metadata"] = {
                    **metadata,
                    "transcript": result["transcript"],
                    "transcribed_locally": True,
                    "transcription_themes": result.get("key_themes", []),
                    "transcription_sentiment": result.get("sentiment"),
                    "transcription_conviction": result.get("conviction"),
                    "transcription_tickers": result.get("tickers_mentioned", []),
                    "video_duration_seconds": result.get("video_duration_seconds"),
                }
                logger.info(f"  ✓ Transcribed: {len(result['transcript'])} chars, "
                           f"themes: {result.get('key_themes', [])[:3]}")
            else:
                logger.warning(f"  ✗ No transcript returned for {title}")
                failed_count += 1

        except Exception as e:
            logger.error(f"  ✗ Transcription failed for {title}: {e}")
            failed_count += 1

        transcribed_videos.append(video)

    # Clean up temporary audio files
    await cleanup_temp_files(harvester.downloads_dir)

    success_count = len(videos) - failed_count
    logger.info(f"Transcription complete: {success_count}/{len(videos)} succeeded")

    return other_items + transcribed_videos


async def cleanup_temp_files(downloads_dir: Path):
    """Clean up temporary audio/video files after transcription."""
    try:
        if downloads_dir.exists():
            for file in downloads_dir.glob("42macro_*.mp3"):
                try:
                    file.unlink()
                    logger.debug(f"Cleaned up: {file.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete {file}: {e}")

            # Also clean up any partial downloads
            for file in downloads_dir.glob("42macro_*.part*"):
                try:
                    file.unlink()
                except:
                    pass

            logger.info("Cleaned up temporary audio files")
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


async def upload_to_railway(collected_data: list, source: str = "42macro") -> bool:
    """Upload collected data to Railway API."""
    import aiohttp

    railway_url = os.getenv("RAILWAY_API_URL")
    auth_user = os.getenv("AUTH_USERNAME")
    auth_pass = os.getenv("AUTH_PASSWORD")
    if not all([railway_url, auth_user, auth_pass]):
        logger.error("Set RAILWAY_API_URL, AUTH_USERNAME, AUTH_PASSWORD environment variables")
        return False

    endpoint = f"{railway_url}/api/collect/{source}"

    try:
        auth = aiohttp.BasicAuth(auth_user, auth_pass)
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=collected_data, auth=auth) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Successfully uploaded {len(collected_data)} items to Railway")
                    logger.info(f"Railway response: {result.get('message', 'OK')}")
                    return True
                else:
                    logger.error(f"Upload failed: {response.status} - {await response.text()}")
                    return False
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return False


async def run_collection(args):
    """Run the 42macro collection with local transcription."""
    # Get credentials from environment
    email = os.getenv("MACRO42_EMAIL")
    password = os.getenv("MACRO42_PASSWORD")

    if not email or not password:
        logger.error("MACRO42_EMAIL and MACRO42_PASSWORD must be set in .env file")
        sys.exit(1)

    # Determine mode
    use_local_db = args.local_db and not args.railway_api
    headless = not args.headful
    skip_transcription = args.skip_transcription

    logger.info("=" * 60)
    logger.info("Starting 42 Macro Collection")
    logger.info(f"Mode: {'Local DB' if use_local_db else 'Railway API'}")
    logger.info(f"Browser: {'Headless' if headless else 'Visible'}")
    logger.info(f"Transcription: {'Disabled' if skip_transcription else 'Enabled (local)'}")
    if args.dry_run:
        logger.info("DRY RUN - No data will be saved")
    logger.info("=" * 60)

    # Import collector after path setup
    from collectors.macro42_selenium import Macro42Collector

    # Create collector
    collector = Macro42Collector(
        email=email,
        password=password,
        headless=headless
    )

    # Set dry_run mode if requested
    if args.dry_run:
        collector.dry_run = True

    transcribed_count = 0

    try:
        # Step 1: Collect data (PDFs and video URLs)
        collected_items = await collector.collect()

        if not collected_items:
            logger.info("No new items collected")
            return {"status": "success", "collected": 0, "saved": 0, "transcribed": 0}

        logger.info(f"Collected {len(collected_items)} items")

        # Step 2: Transcribe videos locally (if not skipped)
        if not skip_transcription:
            videos_before = len([i for i in collected_items if i.get("content_type") == "video"])
            collected_items = await transcribe_videos_locally(
                collected_items,
                dry_run=args.dry_run
            )
            # Count successfully transcribed
            transcribed_count = len([
                i for i in collected_items
                if i.get("content_type") == "video"
                and i.get("metadata", {}).get("transcribed_locally")
            ])
            logger.info(f"Transcribed {transcribed_count}/{videos_before} videos")

        # Step 3: Save/upload data
        if args.dry_run:
            logger.info(f"[DRY RUN] Would save {len(collected_items)} items")
            saved_count = len(collected_items)
        elif use_local_db:
            saved_count = await collector.save_to_database(collected_items)
        else:
            # Upload to Railway API
            success = await upload_to_railway(collected_items, "42macro")
            saved_count = len(collected_items) if success else 0

        return {
            "status": "success",
            "collected": len(collected_items),
            "saved": saved_count,
            "transcribed": transcribed_count
        }

    except Exception as e:
        logger.exception(f"Collection failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "collected": 0,
            "saved": 0,
            "transcribed": 0
        }


def main():
    parser = argparse.ArgumentParser(description="Run 42 Macro collection locally")
    parser.add_argument(
        "--railway-api",
        action="store_true",
        default=True,
        help="Upload collected data to Railway API (default)"
    )
    parser.add_argument(
        "--local-db",
        action="store_true",
        help="Save to local database instead of Railway"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test collection without saving data"
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Show browser window (disable headless mode for debugging)"
    )
    parser.add_argument(
        "--skip-transcription",
        action="store_true",
        help="Skip local video transcription (upload video URLs only)"
    )
    args = parser.parse_args()

    # Ensure logs directory exists
    (project_root / "logs").mkdir(exist_ok=True)

    # Ensure downloads directory exists
    downloads_dir = project_root / "downloads" / "videos"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    # Run collection
    result = asyncio.run(run_collection(args))

    logger.info("=" * 60)
    logger.info(f"Collection Result: {result['status']}")
    logger.info(f"Collected: {result.get('collected', 0)} items")
    logger.info(f"Transcribed: {result.get('transcribed', 0)} videos")
    logger.info(f"Saved: {result.get('saved', 0)} items")
    logger.info("=" * 60)

    if result["status"] == "error":
        logger.error(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
