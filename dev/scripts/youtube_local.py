#!/usr/bin/env python
"""
YouTube Local Transcription Script

Transcribes YouTube videos that don't have auto-generated captions.
Downloads videos locally using yt-dlp, transcribes with Whisper API,
uploads transcripts to Railway, then deletes local files.

This script handles the ~84% of YouTube videos that lack captions
and therefore couldn't be transcribed via the youtube-transcript-api.

Video Transcription Flow:
1. Fetch videos needing transcription from Railway API
2. Download video locally using yt-dlp (works from residential IP)
3. Extract audio and transcribe with Whisper API
4. Analyze transcript with Claude for themes/sentiment
5. Upload transcript + analysis to Railway API
6. DELETE local video/audio files after successful upload

Usage:
    python youtube_local.py --railway-api    # Upload to Railway (default)
    python youtube_local.py --dry-run        # Test without downloading/uploading
    python youtube_local.py --batch-size 5   # Process 5 videos at a time
    python youtube_local.py --skip-cleanup   # Keep downloaded files (debugging)
"""

import asyncio
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
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
        logging.FileHandler(project_root / "logs" / "youtube_transcription.log")
    ]
)
logger = logging.getLogger(__name__)


async def fetch_videos_needing_transcription(source: str = "youtube") -> List[Dict[str, Any]]:
    """
    Fetch list of videos needing transcription from Railway API.

    Args:
        source: Source name to filter by (default: youtube)

    Returns:
        List of video records needing transcription
    """
    import aiohttp

    railway_url = os.getenv("RAILWAY_API_URL", "https://confluence-production-a32e.up.railway.app")
    auth_user = os.getenv("AUTH_USERNAME", "sames3")
    auth_pass = os.getenv("AUTH_PASSWORD", "Spotswood1")

    endpoint = f"{railway_url}/api/collect/transcription-status"

    try:
        auth = aiohttp.BasicAuth(auth_user, auth_pass)
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, auth=auth) as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract videos for the specified source
                    # Try new format first, fall back to existing API structure
                    videos = data.get("videos_needing_transcription", {}).get(source, [])
                    if not videos:
                        # Fall back to existing API structure
                        videos = data.get("by_source", {}).get(source, {}).get("videos_needing_work", [])

                    logger.info(f"Found {len(videos)} {source} videos needing transcription")
                    return videos
                else:
                    logger.error(f"Failed to fetch status: {response.status} - {await response.text()}")
                    return []
    except Exception as e:
        logger.error(f"Error fetching transcription status: {e}")
        return []


async def upload_transcript_to_railway(
    content_id: int,
    transcript: str,
    analysis: Dict[str, Any]
) -> bool:
    """
    Upload transcript and analysis to Railway API for an existing content record.

    Args:
        content_id: Database ID of the content record
        transcript: Full transcript text
        analysis: Dict with themes, sentiment, conviction, tickers, etc.

    Returns:
        True if upload succeeded
    """
    import aiohttp

    railway_url = os.getenv("RAILWAY_API_URL", "https://confluence-production-a32e.up.railway.app")
    auth_user = os.getenv("AUTH_USERNAME", "sames3")
    auth_pass = os.getenv("AUTH_PASSWORD", "Spotswood1")

    # Use the update-transcript endpoint
    endpoint = f"{railway_url}/api/collect/update-transcript/{content_id}"

    payload = {
        "transcript": transcript,
        "themes": analysis.get("key_themes", []),
        "sentiment": analysis.get("sentiment"),
        "conviction": analysis.get("conviction"),
        "tickers": analysis.get("tickers_mentioned", []),
        "duration_seconds": analysis.get("video_duration_seconds"),
        "transcription_provider": analysis.get("transcription_provider", "whisper_local")
    }

    try:
        auth = aiohttp.BasicAuth(auth_user, auth_pass)
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, auth=auth) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"Upload succeeded for content {content_id}")
                    return True
                else:
                    logger.error(f"Upload failed for {content_id}: {response.status} - {await response.text()}")
                    return False
    except Exception as e:
        logger.error(f"Upload error for {content_id}: {e}")
        return False


async def transcribe_video_locally(
    video: Dict[str, Any],
    harvester: Any,
    downloads_dir: Path,
    dry_run: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Download and transcribe a single video locally.

    Args:
        video: Video record from API (id, url, title, source)
        harvester: TranscriptHarvesterAgent instance
        downloads_dir: Directory for downloaded files
        dry_run: If True, skip actual download/transcription

    Returns:
        Dict with transcript and analysis, or None if failed
    """
    video_url = video.get("url")
    title = video.get("title", "Unknown")
    content_id = video.get("id")

    if dry_run:
        logger.info(f"  [DRY RUN] Would transcribe: {title}")
        return {
            "transcript": "[DRY RUN - no transcript]",
            "key_themes": [],
            "sentiment": "neutral",
            "conviction": 0.5,
            "tickers_mentioned": [],
            "transcription_provider": "dry_run"
        }

    try:
        # Run the harvest pipeline (download -> transcribe -> analyze)
        # Force download mode (skip YouTube captions check since we already know they failed)
        result = await harvester.harvest(
            video_url=video_url,
            source="youtube",
            metadata={"title": title, "content_id": content_id},
            priority="medium",
            force_download=True  # Skip captions, go straight to download
        )

        if result and result.get("transcript"):
            return {
                "transcript": result["transcript"],
                "key_themes": result.get("key_themes", []),
                "sentiment": result.get("sentiment"),
                "conviction": result.get("conviction"),
                "tickers_mentioned": result.get("tickers_mentioned", []),
                "video_duration_seconds": result.get("video_duration_seconds"),
                "transcription_provider": result.get("transcription_provider", "whisper_local")
            }
        else:
            logger.warning(f"  No transcript returned for {title}")
            return None

    except Exception as e:
        logger.error(f"  Transcription failed for {title}: {e}")
        return None


async def cleanup_downloads(downloads_dir: Path, source_prefix: str = "youtube"):
    """
    Clean up downloaded video and audio files.

    Args:
        downloads_dir: Directory containing downloads
        source_prefix: Prefix for files to clean (e.g., youtube_*)
    """
    try:
        if not downloads_dir.exists():
            return

        # Clean up all video/audio file types
        extensions = ["*.mp3", "*.mp4", "*.webm", "*.m4a", "*.wav", "*.part*", "*.ytdl"]
        cleaned = 0

        for ext in extensions:
            for file in downloads_dir.glob(f"{source_prefix}_*{ext}"):
                try:
                    file.unlink()
                    cleaned += 1
                    logger.debug(f"Cleaned up: {file.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete {file}: {e}")

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} temporary files")

    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


async def run_transcription(args):
    """Run the YouTube transcription pipeline."""
    from agents.transcript_harvester import TranscriptHarvesterAgent

    # Ensure directories exist
    downloads_dir = project_root / "downloads" / "videos"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    batch_size = args.batch_size
    dry_run = args.dry_run
    skip_cleanup = args.skip_cleanup

    logger.info("=" * 60)
    logger.info("Starting YouTube Local Transcription")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Cleanup: {'Disabled' if skip_cleanup else 'Enabled'}")
    if dry_run:
        logger.info("DRY RUN - No downloads or uploads")
    logger.info("=" * 60)

    # Step 1: Fetch videos needing transcription
    videos = await fetch_videos_needing_transcription("youtube")

    if not videos:
        logger.info("No YouTube videos need transcription")
        return {
            "status": "success",
            "total_needing": 0,
            "processed": 0,
            "succeeded": 0,
            "failed": 0
        }

    total_needing = len(videos)
    logger.info(f"Total videos needing transcription: {total_needing}")

    # Limit to batch size
    videos_to_process = videos[:batch_size]
    logger.info(f"Processing batch of {len(videos_to_process)} videos")

    # Initialize harvester
    try:
        harvester = TranscriptHarvesterAgent()
    except Exception as e:
        logger.error(f"Failed to initialize TranscriptHarvesterAgent: {e}")
        return {
            "status": "error",
            "error": str(e),
            "total_needing": total_needing,
            "processed": 0,
            "succeeded": 0,
            "failed": 0
        }

    # Step 2: Process each video
    succeeded = 0
    failed = 0

    for i, video in enumerate(videos_to_process):
        title = video.get("title", "Unknown")
        content_id = video.get("id")

        logger.info(f"[{i+1}/{len(videos_to_process)}] Processing: {title}")

        # Transcribe
        result = await transcribe_video_locally(
            video=video,
            harvester=harvester,
            downloads_dir=downloads_dir,
            dry_run=dry_run
        )

        if result:
            # Upload to Railway
            if dry_run:
                logger.info(f"  [DRY RUN] Would upload transcript for {title}")
                succeeded += 1
            else:
                upload_success = await upload_transcript_to_railway(
                    content_id=content_id,
                    transcript=result["transcript"],
                    analysis=result
                )

                if upload_success:
                    logger.info(f"  Transcribed: {len(result['transcript'])} chars, "
                               f"themes: {result.get('key_themes', [])[:3]}")
                    succeeded += 1
                else:
                    logger.error(f"  Upload failed for {title}")
                    failed += 1
        else:
            failed += 1

        # Clean up after each video (unless disabled)
        if not skip_cleanup and not dry_run:
            await cleanup_downloads(downloads_dir, "youtube")

    # Final cleanup
    if not skip_cleanup and not dry_run:
        await cleanup_downloads(downloads_dir, "youtube")

    remaining = total_needing - succeeded

    return {
        "status": "success",
        "total_needing": total_needing,
        "processed": len(videos_to_process),
        "succeeded": succeeded,
        "failed": failed,
        "remaining": remaining
    }


def main():
    parser = argparse.ArgumentParser(
        description="Transcribe YouTube videos locally and upload to Railway"
    )
    parser.add_argument(
        "--railway-api",
        action="store_true",
        default=True,
        help="Upload transcripts to Railway API (default)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test without downloading or uploading"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of videos to process per run (default: 5)"
    )
    parser.add_argument(
        "--skip-cleanup",
        action="store_true",
        help="Keep downloaded files after transcription (for debugging)"
    )
    args = parser.parse_args()

    # Ensure logs directory exists
    (project_root / "logs").mkdir(exist_ok=True)

    # Ensure downloads directory exists
    downloads_dir = project_root / "downloads" / "videos"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    # Run transcription
    result = asyncio.run(run_transcription(args))

    logger.info("=" * 60)
    logger.info(f"Transcription Result: {result['status']}")
    logger.info(f"Total needing transcription: {result.get('total_needing', 0)}")
    logger.info(f"Processed this batch: {result.get('processed', 0)}")
    logger.info(f"Succeeded: {result.get('succeeded', 0)}")
    logger.info(f"Failed: {result.get('failed', 0)}")
    logger.info(f"Remaining: {result.get('remaining', 0)}")
    logger.info("=" * 60)

    if result["status"] == "error":
        logger.error(f"Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)

    # Exit with code based on success rate
    if result.get("failed", 0) > 0 and result.get("succeeded", 0) == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
