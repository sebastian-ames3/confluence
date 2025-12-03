"""
Discord Collector (Local Script)

Collects content from Discord channels using Sebastian's logged-in session.
Uses discord.py-self (not a bot) to access channels.
Runs on local laptop, saves data to database or posts to Railway API.

Security (PRD-015):
- Discord channel config loaded from DISCORD_CHANNELS env var (production)
- Falls back to config file for local development
- Railway URLs loaded from RAILWAY_API_URL env var
"""

import discord
import asyncio
import json
import aiohttp
import re
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)

def get_railway_api_url():
    """Get Railway API URL from environment (read at runtime, not module load)."""
    return os.getenv("RAILWAY_API_URL", "http://localhost:8000")


class DiscordSelfCollector(BaseCollector):
    """
    Discord self-collector using user token.

    Collects from specified channels in Options Insight Discord server.
    Downloads PDFs, images, and extracts video links (Zoom/Webex).
    """

    def __init__(
        self,
        user_token: str,
        config_path: str = "config/discord_channels.json",
        use_local_db: bool = True
    ):
        """
        Initialize Discord collector.

        Args:
            user_token: Discord user token (not bot token)
            config_path: Path to channel configuration file
            use_local_db: If True, save to local database. If False, upload to Railway API
        """
        super().__init__(source_name="discord")

        self.user_token = user_token
        self.config_path = config_path
        self.use_local_db = use_local_db
        self.client = None
        self.channel_config = self._load_config()

        logger.info(f"Initialized DiscordSelfCollector with config from {config_path}")

    def _load_config(self) -> Dict[str, Any]:
        """
        Load Discord channel configuration.

        Priority:
        1. DISCORD_CHANNELS environment variable (production)
        2. Config file at config_path (local development)

        Returns:
            Channel configuration dictionary
        """
        # Check environment variable first (PRD-015)
        env_config = os.getenv("DISCORD_CHANNELS")
        if env_config:
            try:
                config = json.loads(env_config)
                channel_count = len(config.get('channels_to_monitor', []))
                logger.info(f"Loaded {channel_count} channels from DISCORD_CHANNELS env var")
                return config
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in DISCORD_CHANNELS env var: {e}")
                raise ValueError(f"Invalid DISCORD_CHANNELS environment variable: {e}")

        # Fall back to config file for local development
        config_path = Path(self.config_path)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                channel_count = len(config.get('channels_to_monitor', []))
                logger.info(f"Loaded {channel_count} channels from {self.config_path}")
                return config
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config file: {e}")
                raise

        # No config found
        raise ValueError(
            "Discord configuration not found. "
            "Set DISCORD_CHANNELS env var or create config/discord_channels.json"
        )

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect messages from all configured Discord channels.

        Returns:
            List of collected messages with metadata
        """
        collected_data = []

        # Initialize Discord client
        self.client = discord.Client()

        @self.client.event
        async def on_ready():
            logger.info(f'Logged in as {self.client.user}')

            try:
                # Collect from each configured channel
                for channel_config in self.channel_config["channels_to_monitor"]:
                    channel_data = await self._collect_channel(channel_config)
                    collected_data.extend(channel_data)

            except Exception as e:
                logger.error(f"Error during collection: {e}")
                raise
            finally:
                await self.client.close()

        # Start the client
        try:
            await self.client.start(self.user_token)
        except discord.LoginFailure:
            logger.error("Failed to login to Discord. Check your user token.")
            raise
        except Exception as e:
            logger.error(f"Discord client error: {e}")
            raise

        # Send heartbeat to backend
        await self._send_heartbeat()

        return collected_data

    async def _collect_channel(self, channel_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Collect messages from a single Discord channel and its threads.

        Args:
            channel_config: Channel configuration from config file

        Returns:
            List of collected messages
        """
        channel_id = int(channel_config["channel_id"])
        channel = self.client.get_channel(channel_id)

        if not channel:
            logger.warning(f"Channel {channel_config['name']} (ID: {channel_id}) not found!")
            return []

        # Check if this is a Forum channel (requires different handling)
        if hasattr(channel, 'type') and str(channel.type) == 'forum':
            logger.info(f"Collecting from #{channel_config['name']} (Forum)...")
            return await self._collect_forum_channel(channel, channel_config)

        # Determine lookback time
        lookback_time = self._get_lookback_time(channel_config["name"])
        max_messages = self.channel_config["collection_settings"]["max_messages_per_channel"]

        messages_data = []
        message_count = 0

        logger.info(f"Collecting from #{channel_config['name']}...")

        try:
            # Collect from main channel
            async for message in channel.history(limit=max_messages, after=lookback_time):
                # Apply filters
                if not self._should_collect_message(message):
                    continue

                message_data = await self._process_message(message, channel_config)
                if message_data:
                    messages_data.append(message_data)
                    message_count += 1

            # Collect from active threads in the channel
            if hasattr(channel, 'threads'):
                thread_messages = await self._collect_threads(channel, channel_config, lookback_time)
                messages_data.extend(thread_messages)
                message_count += len(thread_messages)
                if thread_messages:
                    logger.info(f"  └─ Collected {len(thread_messages)} messages from threads")

        except discord.Forbidden:
            logger.error(f"No permission to access #{channel_config['name']}")
        except Exception as e:
            logger.error(f"Error collecting from #{channel_config['name']}: {e}")

        logger.info(f"✅ Collected {message_count} messages from #{channel_config['name']}")
        return messages_data

    async def _collect_threads(
        self,
        channel: discord.TextChannel,
        channel_config: Dict[str, Any],
        lookback_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Collect messages from all active threads in a channel.

        Args:
            channel: Discord channel object
            channel_config: Channel configuration
            lookback_time: How far back to collect messages

        Returns:
            List of collected thread messages
        """
        thread_messages = []
        max_messages_per_thread = 100  # Limit messages per thread

        try:
            # Get active threads
            active_threads = channel.threads

            # Also get archived threads if needed
            try:
                archived_threads = []
                async for thread in channel.archived_threads(limit=10):
                    archived_threads.append(thread)
                all_threads = active_threads + archived_threads
            except Exception:
                # If archived thread access fails, just use active threads
                all_threads = active_threads

            for thread in all_threads:
                try:
                    # Check if thread has recent activity
                    if hasattr(thread, 'archive_timestamp'):
                        if thread.archive_timestamp and thread.archive_timestamp < lookback_time:
                            continue

                    thread_msg_count = 0
                    async for message in thread.history(limit=max_messages_per_thread, after=lookback_time):
                        if not self._should_collect_message(message):
                            continue

                        message_data = await self._process_message(message, channel_config)
                        if message_data:
                            thread_messages.append(message_data)
                            thread_msg_count += 1

                    if thread_msg_count > 0:
                        logger.debug(f"    🧵 Thread '{thread.name}': {thread_msg_count} messages")

                except discord.Forbidden:
                    logger.debug(f"    ⚠️  No access to thread '{thread.name}'")
                except Exception as e:
                    logger.debug(f"    ⚠️  Error in thread '{thread.name}': {e}")

        except Exception as e:
            logger.warning(f"Error collecting threads: {e}")

        return thread_messages

    async def _collect_forum_channel(
        self,
        channel: discord.ForumChannel,
        channel_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Collect messages from a Forum channel (collects from forum posts/threads).

        Args:
            channel: Discord Forum channel object
            channel_config: Channel configuration

        Returns:
            List of collected messages from forum threads
        """
        messages_data = []
        lookback_time = self._get_lookback_time(channel_config["name"])
        max_messages_per_thread = 100

        try:
            # Get all active threads in the forum
            threads = channel.threads if hasattr(channel, 'threads') else []

            # Also try to get archived threads
            try:
                archived_threads = []
                async for thread in channel.archived_threads(limit=20):
                    archived_threads.append(thread)
                all_threads = list(threads) + archived_threads
            except Exception:
                all_threads = list(threads)

            logger.info(f"  Found {len(all_threads)} forum threads")

            # Collect messages from each thread
            for thread in all_threads:
                try:
                    thread_msg_count = 0
                    async for message in thread.history(limit=max_messages_per_thread, after=lookback_time):
                        if not self._should_collect_message(message):
                            continue

                        message_data = await self._process_message(message, channel_config)
                        if message_data:
                            messages_data.append(message_data)
                            thread_msg_count += 1

                    if thread_msg_count > 0:
                        logger.debug(f"    Thread '{thread.name}': {thread_msg_count} messages")

                except discord.Forbidden:
                    logger.debug(f"    No access to thread '{thread.name}'")
                except Exception as e:
                    logger.debug(f"    Error in thread '{thread.name}': {e}")

        except Exception as e:
            logger.warning(f"Error collecting from forum channel: {e}")

        logger.info(f"Collected {len(messages_data)} messages from #{channel_config['name']}")
        return messages_data

    async def _process_message(
        self,
        message: discord.Message,
        channel_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single Discord message with full context tracking.

        Args:
            message: Discord message object
            channel_config: Channel configuration

        Returns:
            Processed message data or None
        """
        # Determine content type
        content_type = "text"  # Default
        file_path = None
        url = None

        # Handle attachments (PDFs, images)
        attachments_data = []
        if message.attachments and channel_config["collect_types"]:
            attachments_data = await self._process_attachments(
                message.attachments,
                channel_config["collect_types"]
            )

            # Set content type based on first attachment
            if attachments_data:
                first_attachment = attachments_data[0]
                if first_attachment["type"] == "pdf":
                    content_type = "pdf"
                    file_path = first_attachment["path"]
                elif first_attachment["type"] == "image":
                    content_type = "image"
                    file_path = first_attachment["path"]

        # Extract video links (Zoom, Webex, YouTube)
        video_links = []
        video_transcripts = []
        if "video_links" in channel_config["collect_types"]:
            video_links = self._extract_video_links(message.content)

            # If video link found, set as video content type
            if video_links:
                content_type = "video"
                url = video_links[0]["url"]

                # Download and transcribe Zoom/Webex recordings
                video_transcripts = await self._process_video_links(video_links)

        # Extract mentions
        mentions_data = self._extract_mentions(message)

        # Extract reactions
        reactions_data = self._extract_reactions(message)

        # Check if message is in a thread or is a reply
        thread_data = self._extract_thread_info(message)

        # Build message data
        message_data = {
            "content_type": content_type,
            "content_text": message.content,
            "file_path": file_path,
            "url": url,
            "collected_at": message.created_at.isoformat(),
            "metadata": {
                "channel_name": channel_config["name"],
                "channel_id": str(channel_config["channel_id"]),
                "priority": channel_config["priority"],
                "message_id": str(message.id),
                "author": message.author.name,
                "author_id": str(message.author.id),
                "timestamp": message.created_at.isoformat(),
                "edited_at": message.edited_at.isoformat() if message.edited_at else None,
                "is_edited": message.edited_at is not None,
                "attachments": attachments_data,
                "video_links": video_links,
                "video_transcripts": video_transcripts,
                "mentions": mentions_data,
                "reactions": reactions_data,
                "thread_info": thread_data,
                "embeds": [
                    {
                        "type": embed.type,
                        "url": embed.url,
                        "title": embed.title
                    }
                    for embed in message.embeds
                ] if message.embeds else [],
                "is_pinned": message.pinned,
                "jump_url": message.jump_url
            }
        }

        return message_data

    def _should_collect_message(self, message: discord.Message) -> bool:
        """
        Apply filters to determine if message should be collected.

        Args:
            message: Discord message object

        Returns:
            True if message should be collected
        """
        settings = self.channel_config["collection_settings"]

        # Ignore bot messages
        if message.author.bot:
            return False

        # Check minimum length
        if len(message.content) < settings["min_message_length"]:
            # Allow if has attachments or embeds
            if not message.attachments and not message.embeds:
                return False

        # Check ignore patterns
        content_lower = message.content.lower().strip()
        for pattern in settings["ignore_patterns"]:
            # Simple pattern matching
            pattern_clean = pattern.strip("^").strip("$")
            if pattern.startswith("^") and pattern.endswith("$"):
                # Exact match
                if content_lower == pattern_clean:
                    return False
            elif pattern.startswith("^"):
                # Starts with
                if content_lower.startswith(pattern_clean):
                    return False

        return True

    async def _process_attachments(
        self,
        attachments: List[discord.Attachment],
        collect_types: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Download and process message attachments.

        Args:
            attachments: List of Discord attachments
            collect_types: Types of content to collect

        Returns:
            List of processed attachment data
        """
        processed = []
        file_settings = self.channel_config["file_settings"]

        for attachment in attachments:
            # Check file size limit
            size_mb = attachment.size / (1024 * 1024)
            if size_mb > file_settings["max_file_size_mb"]:
                logger.warning(f"⚠️  Skipping {attachment.filename} (too large: {size_mb:.1f}MB)")
                continue

            # Handle PDFs
            if attachment.filename.lower().endswith('.pdf') and "pdfs" in collect_types:
                if file_settings["download_pdfs"]:
                    file_path = await self._download_file(attachment)
                    processed.append({
                        "type": "pdf",
                        "filename": attachment.filename,
                        "path": str(file_path),
                        "size_mb": round(size_mb, 2),
                        "url": attachment.url
                    })

            # Handle images
            elif attachment.content_type and attachment.content_type.startswith('image/'):
                if "images" in collect_types and file_settings["download_images"]:
                    file_path = await self._download_file(attachment)
                    processed.append({
                        "type": "image",
                        "filename": attachment.filename,
                        "path": str(file_path),
                        "size_mb": round(size_mb, 2),
                        "content_type": attachment.content_type
                    })

        return processed

    async def _download_file(self, attachment: discord.Attachment) -> Path:
        """
        Download a file attachment.

        Args:
            attachment: Discord attachment object

        Returns:
            Path to downloaded file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{attachment.filename}"
        file_path = self.download_dir / filename

        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as response:
                with open(file_path, 'wb') as f:
                    f.write(await response.read())

        logger.info(f"Downloaded {attachment.filename} to {file_path}")
        return file_path

    def _extract_video_links(self, content: str) -> List[Dict[str, str]]:
        """
        Extract Zoom, Webex, YouTube links from message content.

        Args:
            content: Message text content

        Returns:
            List of found video links with platform info
        """
        video_patterns = [
            (r'https://[a-z0-9\.\-]*zoom\.us/rec/[^\s]+', 'zoom'),
            (r'https://[a-z0-9\.\-]*webex\.com/[^\s]+', 'webex'),
            (r'https://[a-z0-9\.\-]*youtube\.com/watch\?v=[^\s]+', 'youtube'),
            (r'https://youtu\.be/[^\s]+', 'youtube'),
        ]

        found_links = []
        for pattern, platform in video_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                found_links.append({
                    "platform": platform,
                    "url": match
                })

        return found_links

    async def _extract_and_transcribe_audio(self, video_url: str, platform: str) -> Optional[Dict[str, Any]]:
        """
        Extract audio from Zoom/Webex recording using yt-dlp and transcribe with Whisper.

        Args:
            video_url: URL to the video recording
            platform: 'zoom' or 'webex'

        Returns:
            Dictionary with transcript and metadata, or None if failed
        """
        # Skip YouTube - handled by separate collector
        if platform == "youtube":
            return None

        audio_dir = self.download_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # yt-dlp adds extension automatically, so we specify without .mp3
        audio_base = audio_dir / f"{timestamp}_{platform}_audio"
        audio_path = audio_dir / f"{timestamp}_{platform}_audio.mp3"

        try:
            # Extract audio using yt-dlp
            logger.info(f"Extracting audio from {platform} recording using yt-dlp...")

            # Find ffmpeg location (winget installs to this path)
            ffmpeg_path = Path.home() / "AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.0.1-full_build/bin"

            yt_dlp_cmd = [
                "yt-dlp",
                "-x",                          # Extract audio only
                "--audio-format", "mp3",       # Convert to MP3
                "-o", str(audio_base) + ".%(ext)s",  # Output path template
                "--no-playlist",               # Single video only
                "--quiet",                     # Suppress output
                "--no-warnings",               # Suppress warnings
            ]

            # Add ffmpeg location if it exists
            if ffmpeg_path.exists():
                yt_dlp_cmd.extend(["--ffmpeg-location", str(ffmpeg_path)])

            yt_dlp_cmd.append(video_url)

            result = subprocess.run(yt_dlp_cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                logger.warning(f"yt-dlp failed for {video_url[:50]}...: {result.stderr}")
                return None

            # Check if file was created
            if not audio_path.exists():
                # yt-dlp might have used a different extension, check for any audio file
                possible_files = list(audio_dir.glob(f"{timestamp}_{platform}_audio.*"))
                if possible_files:
                    audio_path = possible_files[0]
                else:
                    logger.warning(f"yt-dlp did not create audio file for {video_url[:50]}...")
                    return None

            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            logger.info(f"Extracted audio: {file_size_mb:.1f} MB")

            # Transcribe using Whisper
            transcript_result = await self._transcribe_audio(audio_path)

            if transcript_result:
                transcript_result["platform"] = platform
                transcript_result["url"] = video_url
                transcript_result["transcribed_at"] = datetime.utcnow().isoformat()

            # Delete audio file after transcription (success or failure)
            if audio_path.exists():
                audio_path.unlink()
                logger.info(f"Deleted audio file: {audio_path}")

            return transcript_result

        except subprocess.TimeoutExpired:
            logger.error(f"yt-dlp timed out (>5 min) for {video_url[:50]}...")
            return None
        except Exception as e:
            logger.error(f"Failed to extract/transcribe audio: {e}")
            # Clean up any partial file
            if audio_path.exists():
                audio_path.unlink()
            return None

    async def _transcribe_audio(self, audio_path: Path) -> Optional[Dict[str, Any]]:
        """
        Transcribe an audio file using Whisper.

        Runs transcription in a thread pool to avoid blocking the Discord gateway.

        Args:
            audio_path: Path to the audio file

        Returns:
            Dictionary with transcript text and duration, or None if failed
        """
        try:
            import whisper
            import concurrent.futures

            logger.info(f"Transcribing audio with Whisper (base model, English)...")

            # Add ffmpeg to PATH if not already there (winget installation location)
            ffmpeg_bin = Path.home() / "AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.0.1-full_build/bin"
            if ffmpeg_bin.exists() and str(ffmpeg_bin) not in os.environ.get("PATH", ""):
                os.environ["PATH"] = str(ffmpeg_bin) + os.pathsep + os.environ.get("PATH", "")

            def run_whisper():
                """Run Whisper transcription in a separate thread."""
                # Load model (cached after first load)
                model = whisper.load_model("base")

                # Transcribe with forced English
                return model.transcribe(
                    str(audio_path),
                    language="en",
                    fp16=False  # Use fp32 for CPU compatibility
                )

            # Run in thread pool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(executor, run_whisper)

            transcript_text = result.get("text", "").strip()

            if not transcript_text:
                logger.warning("Whisper returned empty transcript")
                return None

            # Get duration from segments
            segments = result.get("segments", [])
            duration_seconds = 0
            if segments:
                duration_seconds = int(segments[-1].get("end", 0))

            logger.info(f"Transcription complete: {len(transcript_text)} chars, {duration_seconds}s duration")

            return {
                "transcript": transcript_text,
                "duration_seconds": duration_seconds
            }

        except ImportError:
            logger.error("Whisper not installed. Run: pip install openai-whisper")
            return None
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None

    async def _process_video_links(self, video_links: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Process video links to extract audio and transcribe Zoom/Webex recordings.

        Args:
            video_links: List of video link dictionaries with 'platform' and 'url'

        Returns:
            List of transcription results
        """
        transcripts = []

        for link in video_links:
            platform = link.get("platform", "")
            url = link.get("url", "")

            # Only transcribe Zoom and Webex recordings
            if platform in ("zoom", "webex"):
                result = await self._extract_and_transcribe_audio(url, platform)
                if result:
                    transcripts.append(result)

        return transcripts

    def _extract_mentions(self, message: discord.Message) -> Dict[str, Any]:
        """
        Extract all mentions from a Discord message.

        Args:
            message: Discord message object

        Returns:
            Dictionary containing user, role, and channel mentions
        """
        mentions_data = {
            "users": [],
            "roles": [],
            "channels": [],
            "everyone": message.mention_everyone
        }

        # Extract user mentions
        for user in message.mentions:
            mentions_data["users"].append({
                "id": str(user.id),
                "username": user.name,
                "display_name": user.display_name if hasattr(user, 'display_name') else user.name
            })

        # Extract role mentions
        for role in message.role_mentions:
            mentions_data["roles"].append({
                "id": str(role.id),
                "name": role.name
            })

        # Extract channel mentions
        if hasattr(message, 'channel_mentions'):
            for channel in message.channel_mentions:
                mentions_data["channels"].append({
                    "id": str(channel.id),
                    "name": channel.name
                })

        return mentions_data

    def _extract_reactions(self, message: discord.Message) -> List[Dict[str, Any]]:
        """
        Extract reactions from a Discord message.

        Args:
            message: Discord message object

        Returns:
            List of reaction data
        """
        reactions_data = []

        for reaction in message.reactions:
            reaction_info = {
                "emoji": str(reaction.emoji),
                "count": reaction.count,
                "me": reaction.me  # Whether the bot/user reacted
            }

            # Try to get custom emoji details
            if hasattr(reaction.emoji, 'id'):
                reaction_info["emoji_id"] = str(reaction.emoji.id)
                reaction_info["emoji_name"] = reaction.emoji.name
                reaction_info["is_custom"] = True
            else:
                reaction_info["is_custom"] = False

            reactions_data.append(reaction_info)

        return reactions_data

    def _extract_thread_info(self, message: discord.Message) -> Dict[str, Any]:
        """
        Extract thread and reply information from a Discord message.

        Args:
            message: Discord message object

        Returns:
            Dictionary containing thread and reply metadata
        """
        thread_info = {
            "is_in_thread": False,
            "thread_id": None,
            "thread_name": None,
            "is_reply": False,
            "reply_to_message_id": None,
            "reply_to_author_id": None,
            "reply_to_author_name": None
        }

        # Check if message is in a Discord thread
        if hasattr(message.channel, 'parent') and message.channel.parent is not None:
            thread_info["is_in_thread"] = True
            thread_info["thread_id"] = str(message.channel.id)
            thread_info["thread_name"] = message.channel.name

        # Check if message is a reply (message reference)
        if message.reference is not None:
            thread_info["is_reply"] = True
            thread_info["reply_to_message_id"] = str(message.reference.message_id)

            # Try to get the referenced message details
            if message.reference.resolved is not None:
                referenced_msg = message.reference.resolved
                thread_info["reply_to_author_id"] = str(referenced_msg.author.id)
                thread_info["reply_to_author_name"] = referenced_msg.author.name

        return thread_info

    def _get_lookback_time(self, channel_name: str) -> datetime:
        """
        Determine how far back to collect messages.

        Checks database for last collection time. Falls back to configured
        lookback_days if no previous collection exists.

        Args:
            channel_name: Name of the channel

        Returns:
            Datetime to start collecting from
        """
        # Try to get last collection time from database
        if self.use_local_db:
            try:
                from backend.models import SessionLocal, Source

                db = SessionLocal()
                source = db.query(Source).filter(Source.name == "discord").first()
                db.close()

                if source and source.last_collected_at:
                    logger.info(f"Using last collection time from database: {source.last_collected_at}")
                    # Add small buffer to avoid missing messages at the boundary
                    return source.last_collected_at - timedelta(minutes=5)
            except Exception as e:
                logger.warning(f"Could not get last collection time from database: {e}")

        # Fall back to configured lookback days for first run
        lookback_days = self.channel_config["collection_settings"]["lookback_days_first_run"]
        logger.info(f"Using configured lookback: {lookback_days} days")
        return datetime.utcnow() - timedelta(days=lookback_days)

    async def upload_to_railway(self, collected_data: List[Dict[str, Any]]) -> bool:
        """
        Upload collected data to Railway API.

        Args:
            collected_data: List of collected messages

        Returns:
            True if upload successful
        """
        railway_url = f"{get_railway_api_url()}/api/collect/discord"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(railway_url, json=collected_data) as response:
                    if response.status == 200:
                        logger.info("✅ Data uploaded to Railway successfully")
                        return True
                    else:
                        logger.error(f"❌ Upload failed: {response.status}")
                        logger.error(await response.text())
                        return False
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return False

    async def run(self) -> Dict[str, Any]:
        """
        Run the full collection process.

        Overrides base class to handle local vs Railway upload.

        Returns:
            Summary of collection results
        """
        start_time = datetime.now()
        logger.info(f"Starting Discord collection...")

        try:
            # Collect content
            content_items = await self.collect()

            if not content_items:
                logger.info("ℹ️  No new messages to collect")
                return {
                    "source": self.source_name,
                    "status": "success",
                    "collected": 0,
                    "saved": 0,
                    "elapsed_seconds": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.utcnow().isoformat()
                }

            # Save data (local DB or Railway API)
            if self.use_local_db:
                saved_count = await self.save_to_database(content_items)
                upload_success = True
            else:
                upload_success = await self.upload_to_railway(content_items)
                saved_count = len(content_items) if upload_success else 0

            elapsed_time = (datetime.now() - start_time).total_seconds()

            result = {
                "source": self.source_name,
                "status": "success" if upload_success else "partial",
                "collected": len(content_items),
                "saved": saved_count,
                "elapsed_seconds": round(elapsed_time, 2),
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(
                f"Collection complete: {saved_count}/{len(content_items)} items saved "
                f"in {elapsed_time:.2f}s"
            )

            return result

        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Collection failed for {self.source_name}: {str(e)}")

            return {
                "source": self.source_name,
                "status": "error",
                "error": str(e),
                "elapsed_seconds": round(elapsed_time, 2),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _send_heartbeat(self):
        """
        Send heartbeat to Railway backend to indicate collector is alive.

        This is critical for monitoring - if heartbeats stop, dashboard shows alert.
        """
        # Use Railway URL from environment (PRD-015)
        railway_url = f"{get_railway_api_url()}/api/heartbeat/discord"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(railway_url) as response:
                    if response.status == 200:
                        logger.info("✓ Heartbeat sent to Railway")
                    else:
                        logger.warning(f"Heartbeat response: {response.status}")
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            # Don't raise - heartbeat failure shouldn't block collection
