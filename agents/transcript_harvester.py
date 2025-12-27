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

        # Create OpenAI client with explicit httpx client to avoid proxy issues on Railway
        import httpx
        http_client = httpx.Client()
        self.openai_client = openai.OpenAI(
            api_key=self.openai_api_key,
            http_client=http_client
        )

        # Initialize AssemblyAI client if API key available (PRD-042)
        self.assemblyai_api_key = os.getenv("ASSEMBLYAI_API_KEY")
        self.assemblyai_client = None
        if self.assemblyai_api_key:
            try:
                import assemblyai as aai
                aai.settings.api_key = self.assemblyai_api_key
                self.assemblyai_client = aai.Transcriber()
                logger.info("AssemblyAI client initialized (primary transcription with speaker diarization)")
            except ImportError:
                logger.warning("AssemblyAI package not installed, using Whisper only")
        else:
            logger.info("ASSEMBLYAI_API_KEY not found, using Whisper as primary transcription")

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
            audio_file = await self.download_and_extract_audio(video_url, source, metadata)

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

    # Path to 42macro cookies file (saved by macro42_selenium.py)
    MACRO42_COOKIES_FILE = "temp/42macro_cookies.json"

    async def download_and_extract_audio(
        self,
        video_url: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Download video and extract audio.

        Args:
            video_url: URL to video
            source: Source identifier
            metadata: Optional metadata with embed_url for Vimeo auth

        Returns:
            Path to extracted audio file (MP3)
        """
        if metadata is None:
            metadata = {}

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_source = source.replace("/", "_").replace(":", "_")

            # Output paths
            video_path = self.downloads_dir / f"{safe_source}_{timestamp}"
            audio_path = self.downloads_dir / f"{safe_source}_{timestamp}.mp3"

            logger.info(f"Downloading video from: {video_url}")

            # Build yt-dlp command with source-specific options
            cmd = self._build_ytdlp_command(
                video_url=video_url,
                source=source,
                metadata=metadata,
                output_path=str(video_path)
            )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"yt-dlp error: {result.stderr}")

                # For 42macro, try embed_url as fallback if main URL fails
                if source == "42macro" and metadata.get("embed_url"):
                    logger.info("Retrying with embed URL for 42macro...")
                    embed_url = metadata["embed_url"]
                    cmd = self._build_ytdlp_command(
                        video_url=embed_url,
                        source=source,
                        metadata=metadata,
                        output_path=str(video_path)
                    )
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    if result.returncode != 0:
                        logger.error(f"yt-dlp embed URL error: {result.stderr}")
                        raise Exception(f"Video download failed (both URLs): {result.stderr}")
                else:
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

    def _build_ytdlp_command(
        self,
        video_url: str,
        source: str,
        metadata: Dict[str, Any],
        output_path: str
    ) -> List[str]:
        """
        Build yt-dlp command with source-specific options.

        Args:
            video_url: URL to download
            source: Source identifier (42macro, youtube, etc.)
            metadata: Metadata with platform info
            output_path: Output file path

        Returns:
            yt-dlp command as list of arguments
        """
        # Base command
        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",  # Get best audio quality
            "-x",  # Extract audio
            "--audio-format", "mp3",  # Convert to MP3
            "--audio-quality", "0",  # Best quality
            "-o", output_path,  # Output template
            "--no-playlist",  # Don't download playlists
            "--no-warnings",  # Suppress warnings
            "--retries", "3",
            "--fragment-retries", "3",
        ]

        # Source-specific options
        if source == "42macro":
            # 42macro uses private Vimeo embeds - need correct referer and cookies
            logger.info("Using 42macro-specific download options (referer + cookies)")
            cmd.extend([
                "--referer", "https://app.42macro.com/",
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ])

            # Add cookies if available
            cookies_path = Path(self.MACRO42_COOKIES_FILE)
            if cookies_path.exists():
                # Convert JSON cookies to Netscape format for yt-dlp
                netscape_cookies = self._convert_cookies_to_netscape(cookies_path)
                if netscape_cookies:
                    cmd.extend(["--cookies", str(netscape_cookies)])
                    logger.info(f"Using 42macro cookies from {netscape_cookies}")
            else:
                logger.warning(f"42macro cookies not found at {cookies_path}")

        elif source == "youtube" or "youtube.com" in video_url:
            # YouTube-specific options
            cmd.extend([
                "--extractor-args", "youtube:player_client=android",
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "--referer", "https://www.youtube.com/",
            ])

        else:
            # Generic options for other platforms
            cmd.extend([
                "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "--referer", "https://www.google.com/",
            ])

        # Add the video URL last
        cmd.append(video_url)

        return cmd

    def _convert_cookies_to_netscape(self, json_cookies_path: Path) -> Optional[Path]:
        """
        Convert JSON cookies (from Selenium) to Netscape format for yt-dlp.

        Args:
            json_cookies_path: Path to JSON cookies file

        Returns:
            Path to Netscape format cookies file, or None if conversion fails
        """
        import json

        try:
            with open(json_cookies_path, "r") as f:
                cookies = json.load(f)

            # Create Netscape format cookies file
            netscape_path = json_cookies_path.parent / "42macro_cookies_netscape.txt"

            with open(netscape_path, "w") as f:
                # Netscape cookie file header
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# This file was generated from 42macro Selenium cookies\n\n")

                for cookie in cookies:
                    # Netscape format: domain, include_subdomains, path, secure, expiry, name, value
                    domain = cookie.get("domain", "")
                    # Handle domain starting with . for subdomain matching
                    include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
                    path = cookie.get("path", "/")
                    secure = "TRUE" if cookie.get("secure", False) else "FALSE"
                    expiry = str(int(cookie.get("expiry", 0))) if cookie.get("expiry") else "0"
                    name = cookie.get("name", "")
                    value = cookie.get("value", "")

                    # Write cookie line
                    f.write(f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")

            logger.info(f"Converted {len(cookies)} cookies to Netscape format")
            return netscape_path

        except Exception as e:
            logger.warning(f"Failed to convert cookies to Netscape format: {e}")
            return None

    async def transcribe(self, audio_file: Path) -> Dict[str, Any]:
        """
        Transcribe audio using AssemblyAI (primary) or Whisper (fallback).

        PRD-042: AssemblyAI provides speaker diarization for financial videos.

        Args:
            audio_file: Path to audio file

        Returns:
            Transcript with timestamps and optional speaker labels
        """
        # Try AssemblyAI first if available (PRD-042)
        if self.assemblyai_client:
            try:
                logger.info("Transcribing with AssemblyAI (speaker diarization enabled)")
                return await self._transcribe_assemblyai(audio_file)
            except Exception as e:
                logger.warning(f"AssemblyAI transcription failed, falling back to Whisper: {e}")

        # Fallback to Whisper
        logger.info("Transcribing with Whisper")
        return await self._transcribe_whisper(audio_file)

    async def _transcribe_assemblyai(self, audio_file: Path) -> Dict[str, Any]:
        """
        Transcribe audio using AssemblyAI with speaker diarization.

        PRD-042: Primary transcription method with speaker labels.

        Args:
            audio_file: Path to audio file

        Returns:
            Transcript with timestamps and speaker labels
        """
        import assemblyai as aai

        logger.info(f"AssemblyAI transcribing: {audio_file}")

        # Configure transcription with speaker diarization
        config = aai.TranscriptionConfig(
            speaker_labels=True,  # Enable speaker diarization
            language_code="en"
        )

        # Transcribe (AssemblyAI handles any file size)
        transcript = self.assemblyai_client.transcribe(
            str(audio_file),
            config=config
        )

        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"AssemblyAI transcription failed: {transcript.error}")

        # Convert utterances to segment format with speaker labels
        segments = []
        for i, utterance in enumerate(transcript.utterances or []):
            segments.append({
                "id": i,
                "start": utterance.start / 1000,  # Convert ms to seconds
                "end": utterance.end / 1000,
                "text": utterance.text,
                "speaker": utterance.speaker  # "A", "B", etc.
            })

        # Count unique speakers
        speakers = set(u.speaker for u in transcript.utterances or [])
        speaker_count = len(speakers)

        logger.info(f"AssemblyAI transcription complete. Length: {len(transcript.text)} characters")
        logger.info(f"Segments: {len(segments)}, Speakers detected: {speaker_count}")

        return {
            "text": transcript.text,
            "segments": segments,
            "duration": transcript.audio_duration,
            "speaker_count": speaker_count,
            "transcription_provider": "assemblyai"
        }

    async def _transcribe_whisper(self, audio_file: Path) -> Dict[str, Any]:
        """
        Transcribe audio using OpenAI Whisper API.

        Fallback transcription method when AssemblyAI is unavailable.

        Args:
            audio_file: Path to audio file

        Returns:
            Transcript with timestamps (no speaker labels)
        """
        try:
            logger.info(f"Whisper transcribing: {audio_file}")

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

            # Convert segments to dict format for consistency
            segment_list = []
            for i, seg in enumerate(segments):
                segment_dict = {
                    "id": i,
                    "start": getattr(seg, 'start', seg.get('start', 0) if isinstance(seg, dict) else 0),
                    "end": getattr(seg, 'end', seg.get('end', 0) if isinstance(seg, dict) else 0),
                    "text": getattr(seg, 'text', seg.get('text', '') if isinstance(seg, dict) else '')
                }
                segment_list.append(segment_dict)

            logger.info(f"Whisper transcription complete. Length: {len(transcript_text)} characters")
            logger.info(f"Segments: {len(segment_list)}")

            return {
                "text": transcript_text,
                "segments": segment_list,
                "duration": transcript_response.duration if hasattr(transcript_response, 'duration') else None,
                "transcription_provider": "whisper"
            }

        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
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
            "chunk_count": len(chunks),
            "transcription_provider": "whisper"
        }

    async def analyze_transcript(
        self,
        transcript: Dict[str, Any],
        metadata: Dict[str, Any],
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Analyze transcript with Claude to extract insights.

        PRD-042: Enhanced to handle speaker diarization from AssemblyAI.

        Args:
            transcript: Transcript dict with text, segments, and optional speaker labels
            metadata: Video metadata (speaker, date, title)
            priority: Priority tier for prompt selection

        Returns:
            Structured analysis with optional speaker attribution
        """
        try:
            transcript_text = transcript["text"]
            speaker = metadata.get("speaker", "Unknown")
            date = metadata.get("date", datetime.now().strftime("%Y-%m-%d"))
            title = metadata.get("title", "Market Analysis")

            logger.info(f"Analyzing transcript for: {speaker} - {title}")

            # Check if transcript has speaker diarization (PRD-042)
            segments = transcript.get("segments", [])
            has_speakers = any(seg.get("speaker") for seg in segments)
            speaker_count = transcript.get("speaker_count", 0)

            if has_speakers:
                logger.info(f"Speaker diarization detected: {speaker_count} speakers")

            # Select system prompt based on priority
            if priority.lower() == "high":
                system_prompt = self.TIER1_SYSTEM_PROMPT
            elif priority.lower() == "medium":
                system_prompt = self.TIER2_SYSTEM_PROMPT
            else:
                system_prompt = self.TIER3_SYSTEM_PROMPT

            # Build speaker-aware instructions (PRD-042)
            if has_speakers:
                speaker_instruction = """
- This transcript includes speaker diarization (Speaker A, B, etc.)
- For key_quotes: Include the speaker label (e.g., {"speaker": "A", "timestamp": "...", "text": "..."})
- Note if different speakers have conflicting views on a topic
- Try to identify which speaker is the host vs guest/analyst based on context
- Weight opinions from different speakers appropriately (analysts may have more conviction than hosts asking questions)"""
            else:
                speaker_instruction = ""

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
        {{"timestamp": "HH:MM:SS", "text": "quote text", "speaker": "A or B (if available)"}},
        ...
    ]
}}

Instructions:
- Focus on ACTIONABLE insights, not general commentary
- For key_quotes: Extract 3-5 most important quotes with timestamps
- For conviction: Rate 0-10 based on speaker's confidence and data backing
- For falsification_criteria: Be specific (e.g., "If VIX drops below 15", not "if market rallies")
- If speaker discusses multiple distinct theses, focus on the primary/strongest one{speaker_instruction}

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
            analysis["transcript_segments"] = segments
            analysis["video_duration_seconds"] = transcript.get("duration")

            # Add transcription metadata (PRD-042)
            analysis["transcription_provider"] = transcript.get("transcription_provider", "unknown")
            if has_speakers:
                analysis["speaker_count"] = speaker_count

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
