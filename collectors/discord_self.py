"""
Discord Collector (Local Script)

Collects content from Discord channels using Sebastian's logged-in session.
Uses discord.py-self (not a bot) to access channels.
Runs on local laptop, saves data to database or posts to Railway API.
"""

import discord
import asyncio
import json
import aiohttp
import re
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


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
        """Load channel configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded {len(config['channels_to_monitor'])} channels from config")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            logger.info("Please copy config/discord_channels.json.template to config/discord_channels.json")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise

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
            await self.client.start(self.user_token, bot=False)
        except discord.LoginFailure:
            logger.error("Failed to login to Discord. Check your user token.")
            raise
        except Exception as e:
            logger.error(f"Discord client error: {e}")
            raise

        return collected_data

    async def _collect_channel(self, channel_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Collect messages from a single Discord channel.

        Args:
            channel_config: Channel configuration from config file

        Returns:
            List of collected messages
        """
        channel_id = int(channel_config["channel_id"])
        channel = self.client.get_channel(channel_id)

        if not channel:
            logger.warning(f"⚠️  Channel {channel_config['name']} (ID: {channel_id}) not found!")
            return []

        # Determine lookback time
        lookback_time = self._get_lookback_time(channel_config["name"])
        max_messages = self.channel_config["collection_settings"]["max_messages_per_channel"]

        messages_data = []
        message_count = 0

        logger.info(f"📡 Collecting from #{channel_config['name']}...")

        try:
            async for message in channel.history(limit=max_messages, after=lookback_time):
                # Apply filters
                if not self._should_collect_message(message):
                    continue

                message_data = await self._process_message(message, channel_config)
                if message_data:
                    messages_data.append(message_data)
                    message_count += 1

        except discord.Forbidden:
            logger.error(f"No permission to access #{channel_config['name']}")
        except Exception as e:
            logger.error(f"Error collecting from #{channel_config['name']}: {e}")

        logger.info(f"✅ Collected {message_count} messages from #{channel_config['name']}")
        return messages_data

    async def _process_message(
        self,
        message: discord.Message,
        channel_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single Discord message.

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
        if "video_links" in channel_config["collect_types"]:
            video_links = self._extract_video_links(message.content)

            # If video link found, set as video content type
            if video_links:
                content_type = "video"
                url = video_links[0]["url"]

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
                "attachments": attachments_data,
                "video_links": video_links,
                "embeds": [
                    {
                        "type": embed.type,
                        "url": embed.url,
                        "title": embed.title
                    }
                    for embed in message.embeds
                ] if message.embeds else []
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

    def _get_lookback_time(self, channel_name: str) -> datetime:
        """
        Determine how far back to collect messages.

        Args:
            channel_name: Name of the channel

        Returns:
            Datetime to start collecting from
        """
        # TODO: Check last collection time from database
        # For now, use configured lookback days
        lookback_days = self.channel_config["collection_settings"]["lookback_days_first_run"]
        return datetime.utcnow() - timedelta(days=lookback_days)

    async def upload_to_railway(self, collected_data: List[Dict[str, Any]]) -> bool:
        """
        Upload collected data to Railway API.

        Args:
            collected_data: List of collected messages

        Returns:
            True if upload successful
        """
        railway_url = "https://confluence-production.up.railway.app/api/collect/discord"

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
