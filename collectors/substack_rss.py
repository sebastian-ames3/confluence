"""
Substack RSS Collector

Collects articles and content from Substack RSS feeds.
"""

import logging
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class SubstackCollector(BaseCollector):
    """
    Collector for Substack newsletter content.

    Monitors:
    - Visser Labs (https://visserlabs.substack.com/)
    """

    def __init__(self, substack_urls: Optional[List[str]] = None):
        """
        Initialize Substack collector.

        Args:
            substack_urls: List of Substack URLs to monitor. Defaults to Visser Labs.
        """
        super().__init__(source_name="substack")

        # Default to Visser Labs
        self.substack_urls = substack_urls or [
            "https://visserlabs.substack.com/"
        ]

        logger.info(f"Initialized SubstackCollector with {len(self.substack_urls)} feeds")

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect articles from all configured Substack feeds.

        Returns:
            List of article content items
        """
        collected_articles = []

        for substack_url in self.substack_urls:
            logger.info(f"Collecting from Substack: {substack_url}")

            try:
                articles = self._collect_feed(substack_url)
                collected_articles.extend(articles)
                logger.info(f"Collected {len(articles)} articles from {substack_url}")

            except Exception as e:
                logger.error(f"Error collecting from {substack_url}: {e}")

        logger.info(f"Total Substack articles collected: {len(collected_articles)}")
        return collected_articles

    def _collect_feed(self, substack_url: str, max_articles: int = 20) -> List[Dict[str, Any]]:
        """
        Collect articles from a single Substack feed.

        Args:
            substack_url: Base URL of Substack (e.g., https://example.substack.com/)
            max_articles: Maximum number of articles to collect

        Returns:
            List of article content items
        """
        articles = []

        try:
            # Construct RSS feed URL
            rss_url = self._get_rss_url(substack_url)
            logger.info(f"Fetching RSS feed: {rss_url}")

            # Parse RSS feed
            feed = feedparser.parse(rss_url)

            if feed.bozo and feed.bozo_exception:
                logger.warning(f"Feed parse issue for {rss_url}: {feed.bozo_exception}")
            if not feed.entries:
                logger.warning(f"No entries found in RSS feed: {rss_url}")
                return articles

            # Extract substack name from URL
            substack_name = substack_url.rstrip('/').split('/')[-1].replace('.substack.com', '')
            if not substack_name:
                # Handle case where URL is just "https://visserlabs.substack.com/"
                substack_name = substack_url.split('//')[1].split('.')[0]

            # Process each entry
            for entry in feed.entries[:max_articles]:
                article_data = self._parse_entry(entry, substack_name)
                if article_data:
                    articles.append(article_data)

        except Exception as e:
            logger.error(f"Error parsing RSS feed {substack_url}: {e}")

        return articles

    def _get_rss_url(self, substack_url: str) -> str:
        """
        Convert Substack base URL to RSS feed URL.

        Args:
            substack_url: Base Substack URL

        Returns:
            RSS feed URL
        """
        # Ensure URL ends with /
        if not substack_url.endswith('/'):
            substack_url += '/'

        # Substack RSS feeds are at /feed
        return f"{substack_url}feed"

    def _parse_entry(self, entry: Any, substack_name: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single RSS feed entry into content item.

        Args:
            entry: feedparser entry object
            substack_name: Name of the Substack

        Returns:
            Content item dict or None
        """
        try:
            # Extract basic fields
            title = entry.get('title', 'Untitled')
            link = entry.get('link', '')
            published = entry.get('published', '')
            author = entry.get('author', substack_name)

            # Extract content
            content_html = entry.get('content', [{}])[0].get('value', '') or entry.get('summary', '')

            # Clean HTML to get text
            content_text = self._clean_html(content_html)

            # Parse published date
            published_dt = None
            if published:
                try:
                    # feedparser provides struct_time
                    published_struct = entry.get('published_parsed')
                    if published_struct:
                        published_dt = datetime(*published_struct[:6])
                except Exception as e:
                    logger.warning(f"Failed to parse date for article '{entry.get('title', 'unknown')}': {e}")

            # Build article data
            article_data = {
                "content_type": "article",
                "url": link,
                "content_text": f"{title}\n\n{content_text}",
                "collected_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "title": title,
                    "author": author,
                    "substack_name": substack_name,
                    "published_at": published_dt.isoformat() if published_dt else None,
                    "original_published": published,
                    "content_html": content_html,
                    "word_count": len(content_text.split()),
                    "has_images": '<img' in content_html.lower()
                }
            }

            return article_data

        except Exception as e:
            logger.error(f"Error parsing RSS entry: {e}")
            return None

    def _clean_html(self, html: str) -> str:
        """
        Convert HTML to clean text.

        Args:
            html: HTML content

        Returns:
            Clean text content
        """
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            logger.warning(f"Error cleaning HTML: {e}")
            return html

    def get_latest_articles(self, substack_url: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get articles published in the last N days.

        Args:
            substack_url: Substack URL to check
            days: Number of days to look back

        Returns:
            List of recent articles
        """
        all_articles = self._collect_feed(substack_url)
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        recent_articles = []
        for article in all_articles:
            published_str = article['metadata'].get('published_at')
            if published_str:
                try:
                    published_dt = datetime.fromisoformat(published_str)
                    if published_dt >= cutoff_date:
                        recent_articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to parse date for article '{article.get('metadata', {}).get('title', 'unknown')}': {e}")

        return recent_articles
