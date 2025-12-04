"""
Transcript Harvester Agent

Converts video/audio content to transcripts and extracts structured insights.
Uses Whisper API for transcription and Claude for analysis.

Priority Tiers:
- Tier 1 (HIGH): Imran's Discord videos, Darius Dale's 42 Macro videos
- Tier 2 (MEDIUM): Mel's Twitter videos
- Tier 3 (STANDARD): YouTube long-form videos
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import openai
from pydub import AudioSegment

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class TranscriptHarvesterAgent(BaseAgent):
    """
    Agent for transcribing videos and extracting investment insights.

    Pipeline:
    1. Download video (yt-dlp)
    2. Extract audio (ffmpeg/pydub)
    3. Transcribe with Whisper API
    4. Analyze with Claude
    """

    # Priority tier prompts
    TIER1_SYSTEM_PROMPT = """You are analyzing a high-priority financial market analysis video.
This content is data-driven, high production value, and contains dense alpha.
Extract precise details: specific levels, tickers, conviction scores, and actionable insights.
Be thorough and technical."""

    TIER2_SYSTEM_PROMPT = """You are analyzing a market analysis video.
This content is valuable but may include off-topic commentary.
Focus on extracting the main investment thesis and actionable insights.
Filter out casual discussion."""

    TIER3_SYSTEM_PROMPT = """You are analyzing a long-form market discussion video.
This is background content, less time-sensitive.
Extract high-level themes and key insights."""

    def __init__(
        self,
        claude_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        downloads_dir: Optional[Path] = None,
        model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize Transcript Harvester Agent.

        Args:
            claude_api_key: Claude API key (defaults to env var)
            openai_api_key: OpenAI API key for Whisper (defaults to env var)
            downloads_dir: Directory for downloaded videos/audio
            model: Claude model to use
        """
        super().__init__(api_key=claude_api_key, model=model)

        # Initialize OpenAI client for Whisper
        self.openai_api_key = openai_api_key or os.getenv("WHISPER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key required for Whisper. Set WHISPER_API_KEY or OPENAI_API_KEY.")

        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)

        # Setup downloads directory
        if downloads_dir:
            self.downloads_dir = Path(downloads_dir)
        else:
            self.downloads_dir = Path(__file__).parent.parent / "downloads" / "videos"

        self.downloads_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized TranscriptHarvesterAgent")
        logger.info(f"Downloads directory: {self.downloads_dir}")

    async def harvest(
        self,
        video_url: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Full pipeline: video → transcript → analysis.

        Args:
            video_url: URL to video (YouTube, Zoom, Webex, Twitter, etc.)
            source: Source of video (discord, youtube, twitter, 42macro)
            metadata: Optional metadata (speaker, title, date)
            priority: Priority tier (high, medium, standard)

        Returns:
            Complete analysis with transcript and insights
        """
        if metadata is None:
            metadata = {}

        try:
            logger.info(f"Starting harvest for video: {video_url}")
            logger.info(f"Source: {source}, Priority: {priority}")

            # Step 1: Download video and extract audio
            audio_file = await self.download_and_extract_audio(video_url, source)

            # Step 2: Transcribe with Whisper
            transcript = await self.transcribe(audio_file)

            # Step 3: Analyze with Claude
            analysis = await self.analyze_transcript(
                transcript,
                metadata=metadata,
                priority=priority
            )

            # Add original metadata
            analysis["video_url"] = video_url
            analysis["source"] = source
            analysis["priority"] = priority
            analysis["processed_at"] = datetime.utcnow().isoformat()

            logger.info(f"Harvest complete. Extracted {len(analysis.get('key_themes', []))} themes")

            return analysis

        except Exception as e:
            logger.error(f"Harvest failed: {e}")
            raise

    async def download_and_extract_audio(
        self,
        video_url: str,
        source: str
    ) -> Path:
        """
        Download video and extract audio.

        Args:
            video_url: URL to video
            source: Source identifier

        Returns:
            Path to extracted audio file (MP3)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_source = source.replace("/", "_").replace(":", "_")

            # Output paths
            video_path = self.downloads_dir / f"{safe_source}_{timestamp}"
            audio_path = self.downloads_dir / f"{safe_source}_{timestamp}.mp3"

            logger.info(f"Downloading video from: {video_url}")

            # Download video using yt-dlp
            # yt-dlp handles YouTube, Zoom, Webex, Twitter, Vimeo and many other platforms
            cmd = [
                "yt-dlp",
                "-f", "bestaudio/best",  # Get best audio quality
                "-x",  # Extract audio
                "--audio-format", "mp3",  # Convert to MP3
                "--audio-quality", "0",  # Best quality
                "-o", str(video_path),  # Output template
                "--no-playlist",  # Don't download playlists
                "--no-warnings",  # Suppress warnings
                # Use Android client for YouTube to avoid 403 errors
                "--extractor-args", "youtube:player_client=android",
                # Anti-bot measures for YouTube/Vimeo
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "--referer", "https://www.google.com/",
                # Retry on failure
                "--retries", "3",
                "--fragment-retries", "3",
                video_url
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"yt-dlp error: {result.stderr}")
                raise Exception(f"Video download failed: {result.stderr}")

            logger.info(f"Audio extracted to: {audio_path}")

            # Optimize audio for Whisper (16kHz, mono)
            audio = AudioSegment.from_mp3(audio_path)
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(audio_path, format="mp3")

            logger.info(f"Audio optimized for Whisper: 16kHz mono")

            return audio_path

        except subprocess.TimeoutExpired:
            logger.error("Video download timed out")
            raise Exception("Video download timeout (10 minutes)")
        except Exception as e:
            logger.error(f"Download/extraction failed: {e}")
            raise

    async def transcribe(self, audio_file: Path) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper API.

        Args:
            audio_file: Path to audio file

        Returns:
            Transcript with timestamps
        """
        try:
            logger.info(f"Transcribing audio file: {audio_file}")

            # Check file size (Whisper has 25MB limit)
            file_size_mb = audio_file.stat().st_size / (1024 * 1024)
            logger.info(f"Audio file size: {file_size_mb:.2f} MB")

            if file_size_mb > 25:
                logger.warning("File exceeds 25MB, using chunked transcription")
                return await self._transcribe_chunked(audio_file)

            # Transcribe with Whisper
            with open(audio_file, "rb") as audio:
                transcript_response = self.openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    response_format="verbose_json",  # Get timestamps
                    timestamp_granularities=["segment"]  # Segment-level timestamps
                )

            # Extract transcript text and segments
            transcript_text = transcript_response.text
            segments = transcript_response.segments if hasattr(transcript_response, 'segments') else []

            logger.info(f"Transcription complete. Length: {len(transcript_text)} characters")
            logger.info(f"Segments: {len(segments)}")

            return {
                "text": transcript_text,
                "segments": segments,
                "duration": transcript_response.duration if hasattr(transcript_response, 'duration') else None
            }

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    async def _transcribe_chunked(self, audio_file: Path) -> Dict[str, Any]:
        """
        Transcribe large audio files by splitting into chunks.

        Splits audio into 10-minute chunks to stay well under Whisper's 25MB limit.

        Args:
            audio_file: Path to audio file (>25MB)

        Returns:
            Combined transcript with adjusted timestamps
        """
        import tempfile

        logger.info("Starting chunked transcription")

        # Load audio file
        audio = AudioSegment.from_mp3(audio_file)
        total_duration_ms = len(audio)
        total_duration_sec = total_duration_ms / 1000

        logger.info(f"Audio duration: {total_duration_sec:.1f} seconds ({total_duration_sec/60:.1f} minutes)")

        # Split into 10-minute chunks (600,000 ms)
        chunk_duration_ms = 10 * 60 * 1000  # 10 minutes
        chunks = []
        start_ms = 0

        while start_ms < total_duration_ms:
            end_ms = min(start_ms + chunk_duration_ms, total_duration_ms)
            chunks.append({
                "audio": audio[start_ms:end_ms],
                "start_sec": start_ms / 1000,
                "end_sec": end_ms / 1000
            })
            start_ms = end_ms

        logger.info(f"Split audio into {len(chunks)} chunks")

        # Transcribe each chunk
        all_text = []
        all_segments = []

        for i, chunk_data in enumerate(chunks):
            logger.info(f"Transcribing chunk {i+1}/{len(chunks)} ({chunk_data['start_sec']:.0f}s - {chunk_data['end_sec']:.0f}s)")

            # Save chunk to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                chunk_path = Path(tmp_file.name)
                chunk_data["audio"].export(chunk_path, format="mp3")

            try:
                # Transcribe chunk
                with open(chunk_path, "rb") as audio_chunk:
                    response = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_chunk,
                        response_format="verbose_json",
                        timestamp_granularities=["segment"]
                    )

                # Add text
                all_text.append(response.text)

                # Adjust segment timestamps and add to list
                if hasattr(response, 'segments') and response.segments:
                    for segment in response.segments:
                        adjusted_segment = dict(segment) if hasattr(segment, '__dict__') else segment
                        # Adjust timestamps by chunk start time
                        if isinstance(adjusted_segment, dict):
                            adjusted_segment['start'] = adjusted_segment.get('start', 0) + chunk_data['start_sec']
                            adjusted_segment['end'] = adjusted_segment.get('end', 0) + chunk_data['start_sec']
                        all_segments.append(adjusted_segment)

            finally:
                # Clean up temp file
                chunk_path.unlink(missing_ok=True)

        # Combine results
        combined_text = " ".join(all_text)

        logger.info(f"Chunked transcription complete. Total length: {len(combined_text)} characters")
        logger.info(f"Total segments: {len(all_segments)}")

        return {
            "text": combined_text,
            "segments": all_segments,
            "duration": total_duration_sec,
            "chunked": True,
            "chunk_count": len(chunks)
        }

    async def analyze_transcript(
        self,
        transcript: Dict[str, Any],
        metadata: Dict[str, Any],
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Analyze transcript with Claude to extract insights.

        Args:
            transcript: Transcript dict with text and segments
            metadata: Video metadata (speaker, date, title)
            priority: Priority tier for prompt selection

        Returns:
            Structured analysis
        """
        try:
            transcript_text = transcript["text"]
            speaker = metadata.get("speaker", "Unknown")
            date = metadata.get("date", datetime.now().strftime("%Y-%m-%d"))
            title = metadata.get("title", "Market Analysis")

            logger.info(f"Analyzing transcript for: {speaker} - {title}")

            # Select system prompt based on priority
            if priority.lower() == "high":
                system_prompt = self.TIER1_SYSTEM_PROMPT
            elif priority.lower() == "medium":
                system_prompt = self.TIER2_SYSTEM_PROMPT
            else:
                system_prompt = self.TIER3_SYSTEM_PROMPT

            # Build analysis prompt
            user_prompt = f"""Analyze this financial market analysis video transcript.

Speaker: {speaker}
Date: {date}
Title: {title}

Transcript:
{transcript_text}

Extract the following information in JSON format:

{{
    "key_themes": ["list of main macro/market themes discussed"],
    "tickers_mentioned": ["specific securities, indexes, or assets"],
    "sentiment": "bullish|bearish|neutral",
    "conviction": <0-10 integer>,
    "time_horizon": "1d|1w|1m|3m|6m|6m+",
    "catalysts": ["upcoming events that matter for this thesis"],
    "falsification_criteria": ["what would invalidate this view"],
    "key_quotes": [
        {{"timestamp": "HH:MM:SS", "text": "quote text"}},
        ...
    ]
}}

Instructions:
- Focus on ACTIONABLE insights, not general commentary
- For key_quotes: Extract 3-5 most important quotes with timestamps
- For conviction: Rate 0-10 based on speaker's confidence and data backing
- For falsification_criteria: Be specific (e.g., "If VIX drops below 15", not "if market rallies")
- If speaker discusses multiple distinct theses, focus on the primary/strongest one

Return ONLY valid JSON, no markdown formatting."""

            # Call Claude
            analysis = self.call_claude(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=4096,
                temperature=0.0,
                expect_json=True
            )

            # Validate response
            required_fields = [
                "key_themes",
                "tickers_mentioned",
                "sentiment",
                "conviction",
                "time_horizon"
            ]
            self.validate_response_schema(analysis, required_fields)

            # Add transcript to response
            analysis["transcript"] = transcript_text
            analysis["transcript_segments"] = transcript.get("segments", [])
            analysis["video_duration_seconds"] = transcript.get("duration")

            logger.info(f"Analysis complete: {analysis['sentiment']} sentiment, conviction {analysis['conviction']}/10")

            return analysis

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise

    def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Synchronous wrapper for harvest (for BaseAgent compatibility).

        Use harvest() directly for async operation.
        """
        import asyncio
        return asyncio.run(self.harvest(*args, **kwargs))
