"""
Twitter API Collector (Thread-Aware)

Collects tweets from specified accounts using Twitter API v2 (Free Tier).
Intelligently reconstructs threads as single content items.
"""

import os
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import tweepy

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class TwitterCollector(BaseCollector):
    """
    Thread-aware Twitter collector using official Twitter API v2.

    Monitors:
    - @MelMattison1 (Macro trader, economic history, market analysis)

    Features:
    - Thread reconstruction: Multi-tweet threads stitched as single content item
    - Quote tweet handling: Stores URL reference (doesn't fetch to save quota)
    - Media download: Images and videos saved locally
    - Quota tracking: Reports actual API calls made

    Uses Twitter API Free Tier (100 tweets/month limit).
    Collection Strategy: Manual on-demand via dashboard.
    """

    ACCOUNTS = {
        "MelMattison1": None  # Macro/economic history trader
    }

    def __init__(
        self,
        bearer_token: Optional[str] = None,
        accounts: Optional[List[str]] = None
    ):
        """
        Initialize Twitter collector.

        Args:
            bearer_token: Twitter API Bearer Token (from developer portal)
            accounts: List of Twitter usernames. Uses defaults if not provided.
        """
        super().__init__(source_name="twitter")

        self.bearer_token = bearer_token or os.getenv('TWITTER_BEARER_TOKEN')

        if not self.bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN required. Get it from https://developer.twitter.com/")

        self.account_usernames = accounts or list(self.ACCOUNTS.keys())

        # Initialize Twitter API client
        self.client = tweepy.Client(bearer_token=self.bearer_token)

        # Cache for user IDs (to avoid repeated lookups)
        self.user_ids = {}

        # Quota tracking
        self.api_calls_made = 0

        logger.info(f"Initialized TwitterCollector (thread-aware) with {len(self.account_usernames)} accounts")

    async def collect(
        self,
        num_items: int = 10,
        download_media: bool = True
    ) -> Dict[str, Any]:
        """
        Collect tweets/threads from all configured accounts.

        Args:
            num_items: Number of top-level items to collect (threads count as 1)
            download_media: Whether to download images and videos

        Returns:
            Dict with collected content and quota info:
            {
                "content": [tweets/threads],
                "quota_used": int,
                "media_downloaded": {"images": int, "videos": int}
            }
        """
        self.api_calls_made = 0
        all_content = []
        media_stats = {"images": 0, "videos": 0}

        for username in self.account_usernames:
            logger.info(f"Collecting tweets from @{username}")

            try:
                # Get user ID first (required for API call)
                user_id = self._get_user_id(username)

                if not user_id:
                    logger.error(f"Could not find user ID for @{username}")
                    continue

                # Collect tweets with thread awareness
                result = await self._collect_user_content(
                    username,
                    user_id,
                    num_items,
                    download_media
                )

                all_content.extend(result["content"])
                media_stats["images"] += result["media_downloaded"]["images"]
                media_stats["videos"] += result["media_downloaded"]["videos"]

                logger.info(
                    f"Collected {len(result['content'])} items from @{username} "
                    f"({result['quota_used']} API calls)"
                )

            except tweepy.TooManyRequests:
                logger.error(f"Rate limit exceeded for @{username}")
            except tweepy.Forbidden:
                logger.error(f"Access forbidden for @{username} (account may be private)")
            except Exception as e:
                logger.error(f"Error collecting from @{username}: {e}")
                import traceback
                traceback.print_exc()

        logger.info(
            f"Total: {len(all_content)} items collected, "
            f"{self.api_calls_made} API calls, "
            f"{media_stats['images']} images, {media_stats['videos']} videos"
        )

        return {
            "content": all_content,
            "quota_used": self.api_calls_made,
            "media_downloaded": media_stats
        }

    def _get_user_id(self, username: str) -> Optional[str]:
        """
        Get Twitter user ID from username.

        Args:
            username: Twitter username (without @)

        Returns:
            User ID or None
        """
        # Check cache first
        if username in self.user_ids:
            return self.user_ids[username]

        try:
            # Look up user
            user = self.client.get_user(username=username)
            self.api_calls_made += 1

            if user and user.data:
                user_id = user.data.id
                self.user_ids[username] = user_id
                return user_id

        except Exception as e:
            logger.error(f"Error looking up @{username}: {e}")

        return None

    async def _collect_user_content(
        self,
        username: str,
        user_id: str,
        num_items: int,
        download_media: bool
    ) -> Dict[str, Any]:
        """
        Collect tweets/threads from a user with thread reconstruction.

        Args:
            username: Twitter username
            user_id: Twitter user ID
            num_items: Number of top-level items to collect
            download_media: Whether to download media files

        Returns:
            Dict with content and stats
        """
        content = []
        media_stats = {"images": 0, "videos": 0}

        try:
            # Fetch recent tweets (excluding pure retweets, but including replies for thread detection)
            # We'll fetch more than requested to account for threads
            fetch_count = min(num_items * 3, 100)  # Fetch 3x to ensure we get enough thread starters

            response = self.client.get_users_tweets(
                id=user_id,
                max_results=fetch_count,
                tweet_fields=[
                    'created_at',
                    'conversation_id',
                    'in_reply_to_user_id',
                    'referenced_tweets',
                    'public_metrics',
                    'entities',
                    'attachments'
                ],
                media_fields=['url', 'preview_image_url', 'type', 'duration_ms'],
                expansions=['attachments.media_keys', 'referenced_tweets.id'],
                exclude=['retweets']  # Exclude pure retweets, keep replies for threads
            )

            self.api_calls_made += 1

            if not response.data:
                logger.info(f"No tweets found for @{username}")
                return {"content": [], "quota_used": 0, "media_downloaded": media_stats}

            # Get media objects if included
            media_dict = {}
            if hasattr(response, 'includes') and response.includes and 'media' in response.includes:
                for media in response.includes['media']:
                    media_dict[media.media_key] = media

            # Separate thread starters from thread replies
            thread_starters = []
            thread_replies = {}

            for tweet in response.data:
                # Check if this is a reply to someone else (not a self-thread)
                is_reply_to_others = (
                    hasattr(tweet, 'in_reply_to_user_id') and
                    tweet.in_reply_to_user_id and
                    str(tweet.in_reply_to_user_id) != str(user_id)
                )

                # Skip replies to other users
                if is_reply_to_others:
                    continue

                # Check if this is a thread starter (tweet_id == conversation_id)
                is_thread_starter = (
                    not hasattr(tweet, 'in_reply_to_user_id') or
                    tweet.in_reply_to_user_id is None or
                    str(tweet.id) == str(tweet.conversation_id)
                )

                if is_thread_starter:
                    thread_starters.append(tweet)
                else:
                    # This is a self-reply (part of a thread)
                    conv_id = str(tweet.conversation_id)
                    if conv_id not in thread_replies:
                        thread_replies[conv_id] = []
                    thread_replies[conv_id].append(tweet)

            # Limit to requested number of items
            thread_starters = thread_starters[:num_items]

            logger.info(
                f"Found {len(thread_starters)} top-level items, "
                f"{sum(len(replies) for replies in thread_replies.values())} thread replies"
            )

            # Process each thread starter
            for tweet in thread_starters:
                conv_id = str(tweet.conversation_id)

                # Get all replies in this thread (if any)
                replies = thread_replies.get(conv_id, [])

                # Sort replies chronologically
                all_tweets = [tweet] + sorted(replies, key=lambda t: t.created_at)

                # Determine content type
                is_thread = len(all_tweets) > 1
                content_type = "thread" if is_thread else "tweet"

                # Combine text from all tweets in thread
                combined_text = "\n\n".join(t.text for t in all_tweets)

                # Collect all media from thread
                media_urls = []
                downloaded_media = []

                for t in all_tweets:
                    if hasattr(t, 'attachments') and t.attachments:
                        media_keys = t.attachments.get('media_keys', [])
                        for key in media_keys:
                            if key in media_dict:
                                media_obj = media_dict[key]
                                media_info = self._extract_media_info(media_obj)
                                media_urls.append(media_info)

                                # Download media if requested
                                if download_media and media_info['url']:
                                    downloaded_path = await self._download_media(
                                        media_info['url'],
                                        media_info['type'],
                                        username,
                                        str(tweet.id)
                                    )
                                    if downloaded_path:
                                        downloaded_media.append(str(downloaded_path))
                                        if media_info['type'] == 'photo':
                                            media_stats['images'] += 1
                                        elif media_info['type'] == 'video':
                                            media_stats['videos'] += 1

                # Handle quote tweets
                quoted_tweet_ref = None
                if hasattr(tweet, 'referenced_tweets') and tweet.referenced_tweets:
                    for ref in tweet.referenced_tweets:
                        if ref.type == 'quoted':
                            # Store reference only, don't fetch (saves quota)
                            quoted_tweet_ref = {
                                "type": "quoted",
                                "tweet_id": str(ref.id),
                                "url": f"https://twitter.com/i/status/{ref.id}",
                                "note": "Quote tweet reference - not fetched to save quota"
                            }

                # Build content item
                content_item = {
                    "content_type": content_type,
                    "url": f"https://twitter.com/{username}/status/{tweet.id}",
                    "content_text": combined_text,
                    "collected_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "tweet_id": str(tweet.id),
                        "conversation_id": conv_id,
                        "username": username,
                        "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                        "is_thread": is_thread,
                        "thread_length": len(all_tweets),
                        "public_metrics": {
                            "retweet_count": tweet.public_metrics.get('retweet_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                            "reply_count": tweet.public_metrics.get('reply_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                            "like_count": tweet.public_metrics.get('like_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                            "quote_count": tweet.public_metrics.get('quote_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                        },
                        "media": media_urls,
                        "media_count": len(media_urls),
                        "downloaded_media": downloaded_media,
                        "quoted_tweet": quoted_tweet_ref
                    }
                }

                content.append(content_item)

        except Exception as e:
            logger.error(f"Error collecting content for @{username}: {e}")
            import traceback
            traceback.print_exc()

        return {
            "content": content,
            "quota_used": self.api_calls_made,
            "media_downloaded": media_stats
        }

    def _extract_media_info(self, media_obj) -> Dict[str, Any]:
        """
        Extract media information from Twitter media object.

        Args:
            media_obj: Twitter media object from API

        Returns:
            Dict with media info
        """
        media_type = media_obj.type  # 'photo', 'video', 'animated_gif'

        if media_type == 'photo':
            url = media_obj.url
        elif media_type in ['video', 'animated_gif']:
            # For videos, we get preview image but need to use URL to get actual video
            # Twitter API v2 doesn't provide direct video URLs in free tier
            url = getattr(media_obj, 'preview_image_url', None)
        else:
            url = None

        return {
            "type": media_type,
            "url": url,
            "media_key": media_obj.media_key
        }

    async def _download_media(
        self,
        url: str,
        media_type: str,
        username: str,
        tweet_id: str
    ) -> Optional[Path]:
        """
        Download media file (image or video).

        Args:
            url: Media URL
            media_type: 'photo', 'video', 'animated_gif'
            username: Twitter username
            tweet_id: Tweet ID

        Returns:
            Path to downloaded file or None
        """
        try:
            # Determine file extension
            if media_type == 'photo':
                ext = 'jpg'
                subdir = 'images'
            elif media_type == 'video':
                ext = 'mp4'
                subdir = 'videos'
            elif media_type == 'animated_gif':
                ext = 'gif'
                subdir = 'images'
            else:
                logger.warning(f"Unknown media type: {media_type}")
                return None

            # Create directory structure
            media_dir = self.download_dir / subdir
            media_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{username}_{tweet_id}_{timestamp}.{ext}"
            file_path = media_dir / filename

            # Download media
            response = requests.get(url, timeout=30)

            if response.status_code != 200:
                logger.error(f"Failed to download media: {response.status_code}")
                return None

            # Save file
            with open(file_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Downloaded {media_type}: {filename}")
            return file_path

        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None


# For backward compatibility
TwitterAPICollector = TwitterCollector
