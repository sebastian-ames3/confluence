"""
YouTube Collector

Collects videos and metadata from specified channels using YouTube Data API v3.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class YouTubeCollector(BaseCollector):
    """
    Collector for YouTube videos from specified channels.

    Channels monitored:
    - Peter Diamandis
    - Jordi Visser Labs
    - Forward Guidance
    - 42 Macro
    """

    # Channel IDs for monitored channels
    CHANNELS = {
        "peter_diamandis": "UCCpNQKYvrnWQNjZprabMJlw",
        "jordi_visser": "UCSLOw8JrFTBb3qF-p4v0v_w",
        "forward_guidance": "UCEOv-8wHvYC6mzsY2Gm5WcQ",
        "42macro": "UCu0L0QCubkYD3Cd9jSdxTNQ"
    }

    def __init__(self, api_key: str, channels: Optional[Dict[str, str]] = None):
        """
        Initialize YouTube collector.

        Args:
            api_key: YouTube Data API key
            channels: Optional dict of channel_name: channel_id. Uses defaults if not provided.
        """
        super().__init__(source_name="youtube")

        self.api_key = api_key
        self.channels = channels or self.CHANNELS
        self.youtube = build('youtube', 'v3', developerKey=api_key)

        logger.info(f"Initialized YouTubeCollector with {len(self.channels)} channels")

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect videos from all configured channels.

        Returns:
            List of video content items
        """
        collected_videos = []

        for channel_name, channel_id in self.channels.items():
            logger.info(f"Collecting from YouTube channel: {channel_name}")

            try:
                videos = self._collect_channel_videos(channel_id, channel_name)
                collected_videos.extend(videos)
                logger.info(f"Collected {len(videos)} videos from {channel_name}")

            except HttpError as e:
                logger.error(f"YouTube API error for {channel_name}: {e}")
            except Exception as e:
                logger.error(f"Error collecting from {channel_name}: {e}")

        logger.info(f"Total YouTube videos collected: {len(collected_videos)}")
        return collected_videos

    def _collect_channel_videos(
        self,
        channel_id: str,
        channel_name: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Collect recent videos from a specific channel.

        Args:
            channel_id: YouTube channel ID
            channel_name: Human-readable channel name
            max_results: Maximum number of videos to collect

        Returns:
            List of video content items
        """
        videos = []

        try:
            # Get channel's uploads playlist
            channels_response = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()

            if not channels_response.get('items'):
                logger.warning(f"Channel not found: {channel_id}")
                return videos

            # Get uploads playlist ID
            uploads_playlist_id = channels_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

            # Get videos from uploads playlist
            playlist_response = self.youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=max_results
            ).execute()

            # Process each video
            for item in playlist_response.get('items', []):
                video_id = item['contentDetails']['videoId']
                snippet = item['snippet']

                # Get additional video details
                video_details = self._get_video_details(video_id)

                # Build video data
                video_data = {
                    "content_type": "video",
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "content_text": snippet.get('title', ''),
                    "collected_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "video_id": video_id,
                        "channel_name": channel_name,
                        "channel_id": channel_id,
                        "title": snippet.get('title'),
                        "description": snippet.get('description'),
                        "published_at": snippet.get('publishedAt'),
                        "thumbnail_url": snippet.get('thumbnails', {}).get('high', {}).get('url'),
                        "duration": video_details.get('duration'),
                        "view_count": video_details.get('view_count'),
                        "transcript_available": self._check_transcript_available(video_id)
                    }
                }

                videos.append(video_data)

        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise

        return videos

    def _get_video_details(self, video_id: str) -> Dict[str, Any]:
        """
        Get additional details for a video.

        Args:
            video_id: YouTube video ID

        Returns:
            Dict with duration, view count, etc.
        """
        try:
            response = self.youtube.videos().list(
                part='contentDetails,statistics',
                id=video_id
            ).execute()

            if response.get('items'):
                item = response['items'][0]
                return {
                    "duration": item['contentDetails'].get('duration'),
                    "view_count": item['statistics'].get('viewCount'),
                    "like_count": item['statistics'].get('likeCount'),
                    "comment_count": item['statistics'].get('commentCount')
                }

        except Exception as e:
            logger.warning(f"Could not get video details for {video_id}: {e}")

        return {}

    def _check_transcript_available(self, video_id: str) -> bool:
        """
        Check if automatic captions are available for a video.

        Args:
            video_id: YouTube video ID

        Returns:
            True if captions/transcript available
        """
        try:
            response = self.youtube.captions().list(
                part='snippet',
                videoId=video_id
            ).execute()

            return len(response.get('items', [])) > 0

        except HttpError:
            # Captions API may not be accessible with basic API key
            return False
        except Exception as e:
            logger.debug(f"Could not check captions for {video_id}: {e}")
            return False

