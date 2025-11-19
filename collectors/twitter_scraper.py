"""
Twitter Scraper Collector

Collects tweets from specified accounts without Twitter API.
Uses web scraping approach with optional session authentication.
"""

import logging
import requests
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from pathlib import Path

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class TwitterCollector(BaseCollector):
    """
    Collector for Twitter/X content from specified accounts.

    Monitors:
    - @KTTECHPRIVATE (KT Technical Analysis - trade setups)
    - @MelMattison1 (Market analysis)

    Note: Twitter scraping is challenging due to their anti-bot measures.
    This implementation provides multiple approaches:
    1. ntscraper library (recommended if available)
    2. Session-based scraping (requires auth_token cookie)
    3. Placeholder for future API integration
    """

    ACCOUNTS = [
        "KTTECHPRIVATE",
        "MelMattison1"
    ]

    def __init__(
        self,
        accounts: Optional[List[str]] = None,
        auth_token: Optional[str] = None,
        use_ntscraper: bool = True
    ):
        """
        Initialize Twitter collector.

        Args:
            accounts: List of Twitter usernames (without @). Uses defaults if not provided.
            auth_token: Optional Twitter auth_token cookie for authenticated scraping
            use_ntscraper: Try to use ntscraper library if available
        """
        super().__init__(source_name="twitter")

        self.accounts = accounts or self.ACCOUNTS
        self.auth_token = auth_token
        self.use_ntscraper = use_ntscraper
        self.session = requests.Session()

        # Set up session headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        if auth_token:
            self.session.cookies.set('auth_token', auth_token, domain='.twitter.com')

        logger.info(f"Initialized TwitterCollector with {len(self.accounts)} accounts")

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect tweets from all configured accounts.

        Returns:
            List of tweet content items
        """
        collected_tweets = []

        # Try ntscraper first if enabled
        if self.use_ntscraper:
            try:
                tweets = self._collect_with_ntscraper()
                if tweets:
                    logger.info(f"✅ Collected {len(tweets)} tweets using ntscraper")
                    return tweets
            except ImportError:
                logger.warning("ntscraper not available, falling back to manual scraping")
            except Exception as e:
                logger.warning(f"ntscraper failed: {e}, falling back to manual scraping")

        # Fall back to manual scraping
        for account in self.accounts:
            logger.info(f"Collecting tweets from @{account}")

            try:
                tweets = self._collect_account_tweets(account)
                collected_tweets.extend(tweets)
                logger.info(f"✅ Collected {len(tweets)} tweets from @{account}")

            except Exception as e:
                logger.error(f"Error collecting from @{account}: {e}")

        logger.info(f"Total tweets collected: {len(collected_tweets)}")
        return collected_tweets

    def _collect_with_ntscraper(self, max_tweets: int = 50) -> List[Dict[str, Any]]:
        """
        Collect tweets using ntscraper library.

        Args:
            max_tweets: Maximum tweets per account

        Returns:
            List of tweet content items
        """
        try:
            from ntscraper import Nitter

            scraper = Nitter()
            all_tweets = []

            for account in self.accounts:
                logger.info(f"Scraping @{account} with ntscraper...")

                tweets = scraper.get_tweets(account, mode='user', number=max_tweets)

                for tweet in tweets.get('tweets', []):
                    tweet_data = self._parse_ntscraper_tweet(tweet, account)
                    if tweet_data:
                        all_tweets.append(tweet_data)

            return all_tweets

        except ImportError:
            raise
        except Exception as e:
            logger.error(f"ntscraper error: {e}")
            return []

    def _parse_ntscraper_tweet(self, tweet: Dict, account: str) -> Optional[Dict[str, Any]]:
        """
        Parse tweet from ntscraper format to our standard format.

        Args:
            tweet: ntscraper tweet dict
            account: Twitter account username

        Returns:
            Standardized tweet content item
        """
        try:
            tweet_text = tweet.get('text', '')
            tweet_url = tweet.get('link', '')
            created_at = tweet.get('date')

            # Extract media
            media_urls = []
            if 'pictures' in tweet:
                media_urls.extend(tweet.get('pictures', []))
            if 'videos' in tweet:
                media_urls.extend(tweet.get('videos', []))

            # Build tweet data
            tweet_data = {
                "content_type": "tweet",
                "url": tweet_url,
                "content_text": tweet_text,
                "collected_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "username": account,
                    "created_at": created_at,
                    "has_media": len(media_urls) > 0,
                    "media_urls": media_urls,
                    "likes": tweet.get('likes'),
                    "retweets": tweet.get('retweets'),
                    "replies": tweet.get('replies')
                }
            }

            return tweet_data

        except Exception as e:
            logger.error(f"Error parsing ntscraper tweet: {e}")
            return None

    def _collect_account_tweets(
        self,
        account: str,
        max_tweets: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Collect tweets from a single account using manual scraping.

        Args:
            account: Twitter username (without @)
            max_tweets: Maximum number of tweets to collect

        Returns:
            List of tweet content items

        Note: Manual scraping may require authentication and is fragile
        due to Twitter's frequent UI changes.
        """
        tweets = []

        try:
            # This is a placeholder implementation
            # Twitter's actual scraping requires more sophisticated handling:
            # 1. GraphQL API endpoints (requires auth)
            # 2. Selenium for JavaScript rendering
            # 3. Mobile site scraping (easier but still requires auth)

            logger.warning(
                f"Manual Twitter scraping for @{account} not fully implemented. "
                f"Recommend using ntscraper library or providing Twitter API credentials."
            )

            # Placeholder: Would implement mobile.twitter.com scraping here
            # or GraphQL API calls with session authentication

        except Exception as e:
            logger.error(f"Error scraping @{account}: {e}")

        return tweets

    def _download_media(self, media_url: str, tweet_id: str) -> Optional[Path]:
        """
        Download media from tweet.

        Args:
            media_url: URL of media to download
            tweet_id: Tweet ID for filename

        Returns:
            Path to downloaded file or None
        """
        try:
            response = self.session.get(media_url, stream=True)

            if response.status_code != 200:
                logger.error(f"Failed to download media: {response.status_code}")
                return None

            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'image' in content_type:
                ext = '.jpg'
            elif 'video' in content_type:
                ext = '.mp4'
            else:
                ext = ''

            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{tweet_id}{ext}"
            file_path = self.download_dir / filename

            # Save file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded media: {filename}")
            return file_path

        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None


# NOTE: Twitter scraping is challenging and fragile. Recommended approaches:
#
# 1. **ntscraper library** (recommended for MVP):
#    - Install: pip install ntscraper
#    - Uses Nitter instances (Twitter frontends)
#    - No authentication required
#    - May be rate-limited
#
# 2. **Session-based scraping**:
#    - Get auth_token cookie from browser while logged into Twitter
#    - Add to .env: TWITTER_AUTH_TOKEN=your_token_here
#    - Pass to TwitterCollector(auth_token=token)
#    - Requires periodic token refresh
#
# 3. **Twitter API** (if budget allows):
#    - Basic tier: $100/month for 10k tweets/month
#    - Would require switching to official tweepy library
#    - Most reliable long-term solution
#
# 4. **Selenium scraping**:
#    - Use Selenium to render JavaScript
#    - Can use logged-in session from browser
#    - Slower but more reliable
#    - Good for scheduled collection (6am, 6pm)
#
# For Sebastian's use case (2 accounts, ~10-20 tweets/day), I recommend:
# - Start with ntscraper for MVP
# - If that fails, add session-based scraping with his auth_token
# - Consider Twitter API if this becomes critical and budget allows
