"""
Twitter API Collector

Collects tweets from specified accounts using Twitter API v2 (Free Tier).
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import tweepy

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class TwitterCollector(BaseCollector):
    """
    Collector for Twitter/X content using official Twitter API v2.

    Monitors:
    - @KTTECHPRIVATE (KT Technical Analysis - trade setups)
    - @MelMattison1 (Market analysis)

    Uses Twitter API Free Tier (1,500 tweets/month limit).
    """

    ACCOUNTS = {
        "KTTECHPRIVATE": None,  # Will be looked up via API
        "MelMattison1": None
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

        logger.info(f"Initialized TwitterCollector with {len(self.account_usernames)} accounts")

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect tweets from all configured accounts.

        Returns:
            List of tweet content items
        """
        collected_tweets = []

        for username in self.account_usernames:
            logger.info(f"Collecting tweets from @{username}")

            try:
                # Get user ID first (required for API call)
                user_id = self._get_user_id(username)

                if not user_id:
                    logger.error(f"Could not find user ID for @{username}")
                    continue

                # Collect tweets
                tweets = self._collect_user_tweets(username, user_id)
                collected_tweets.extend(tweets)
                logger.info(f"Collected {len(tweets)} tweets from @{username}")

            except tweepy.TooManyRequests:
                logger.error(f"Rate limit exceeded for @{username}")
            except tweepy.Forbidden:
                logger.error(f"Access forbidden for @{username} (account may be private)")
            except Exception as e:
                logger.error(f"Error collecting from @{username}: {e}")

        logger.info(f"Total tweets collected: {len(collected_tweets)}")
        return collected_tweets

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

            if user and user.data:
                user_id = user.data.id
                self.user_ids[username] = user_id
                return user_id

        except Exception as e:
            logger.error(f"Error looking up @{username}: {e}")

        return None

    def _collect_user_tweets(
        self,
        username: str,
        user_id: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Collect recent tweets from a user.

        Args:
            username: Twitter username
            user_id: Twitter user ID
            max_results: Maximum tweets to collect (max 100 per request)

        Returns:
            List of tweet content items
        """
        tweets = []

        try:
            # Get user's tweets
            # Note: Free tier allows tweet_fields but limited expansions
            response = self.client.get_users_tweets(
                id=user_id,
                max_results=min(max_results, 100),  # API max is 100
                tweet_fields=[
                    'created_at',
                    'public_metrics',
                    'entities',
                    'referenced_tweets'
                ],
                exclude=['retweets', 'replies']  # Only original tweets
            )

            if not response.data:
                logger.info(f"No tweets found for @{username}")
                return tweets

            # Process each tweet
            for tweet in response.data:
                tweet_data = self._parse_tweet(tweet, username)
                if tweet_data:
                    tweets.append(tweet_data)

        except Exception as e:
            logger.error(f"Error fetching tweets for @{username}: {e}")

        return tweets

    def _parse_tweet(self, tweet: tweepy.Tweet, username: str) -> Optional[Dict[str, Any]]:
        """
        Parse tweet into standard content format.

        Args:
            tweet: tweepy.Tweet object
            username: Twitter username

        Returns:
            Standardized tweet content item
        """
        try:
            # Extract URLs if present
            urls = []
            if hasattr(tweet, 'entities') and tweet.entities:
                if 'urls' in tweet.entities:
                    urls = [url['expanded_url'] for url in tweet.entities['urls']]

            # Build tweet data
            tweet_data = {
                "content_type": "tweet",
                "url": f"https://twitter.com/{username}/status/{tweet.id}",
                "content_text": tweet.text,
                "collected_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "tweet_id": str(tweet.id),
                    "username": username,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                    "retweet_count": tweet.public_metrics.get('retweet_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                    "reply_count": tweet.public_metrics.get('reply_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                    "like_count": tweet.public_metrics.get('like_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                    "quote_count": tweet.public_metrics.get('quote_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                    "urls": urls,
                    "has_urls": len(urls) > 0
                }
            }

            return tweet_data

        except Exception as e:
            logger.error(f"Error parsing tweet: {e}")
            return None


# For backward compatibility, keep old class name as alias
# This allows existing code to still import TwitterCollector
TwitterAPICollector = TwitterCollector
