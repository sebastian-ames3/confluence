"""
KT Technical Analysis Website Collector

Collects weekly research blog posts from kttechnicalanalysis.com.
Simple session-based authentication with blog post scraping.
"""

import os
import re
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class KTTechnicalCollector(BaseCollector):
    """
    Collector for KT Technical Analysis website.

    Collects:
    - Weekly blog posts (published Sundays)
    - Price chart images
    - Synopsis text for stock/asset price action
    """

    BASE_URL = "https://kttechnicalanalysis.com"
    LOGIN_URL = f"{BASE_URL}/login"
    BLOG_URL = f"{BASE_URL}/blog-feed/"

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize KT Technical collector.

        Args:
            email: Login email (defaults to KT_EMAIL env var)
            password: Login password (defaults to KT_PASSWORD env var)
        """
        super().__init__(source_name="kt_technical")

        self.email = email or os.getenv('KT_EMAIL')
        self.password = password or os.getenv('KT_PASSWORD')

        if not self.email or not self.password:
            raise ValueError("KT_EMAIL and KT_PASSWORD required")

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        logger.info("Initialized KTTechnicalCollector")

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect blog posts from KT Technical Analysis.

        Returns:
            List of blog post content items
        """
        collected_items = []

        try:
            # Login
            if not self._login():
                raise Exception("Login failed")

            # Collect blog posts
            logger.info("Collecting blog posts from KT Technical...")
            posts = self._collect_blog_posts()
            collected_items.extend(posts)
            logger.info(f"Collected {len(posts)} blog posts")

        except Exception as e:
            logger.error(f"Error collecting from KT Technical: {e}")
            raise

        logger.info(f"Total items collected from KT Technical: {len(collected_items)}")
        return collected_items

    def _login(self) -> bool:
        """
        Login to KT Technical Analysis website.

        Returns:
            True if login successful
        """
        try:
            logger.info("Logging in to KT Technical...")

            # Get login page first (to get CSRF token if needed)
            login_page = self.session.get(self.LOGIN_URL, timeout=10)

            if login_page.status_code != 200:
                logger.error(f"Failed to load login page: {login_page.status_code}")
                return False

            # Parse login page to find form fields
            soup = BeautifulSoup(login_page.content, 'html.parser')

            # Build login payload
            # Note: KT Technical uses 'log' and 'pwd' instead of 'email' and 'password'
            login_data = {
                'log': self.email,
                'pwd': self.password
            }

            # Add all hidden fields (includes mepr_process_login_form, etc.)
            hidden_fields = soup.find_all('input', {'type': 'hidden'})
            for field in hidden_fields:
                name = field.get('name')
                value = field.get('value')
                if name:
                    login_data[name] = value

            # Look for CSRF token (in addition to hidden fields)
            csrf_token = soup.find('input', {'name': re.compile(r'csrf|token', re.I)})
            if csrf_token and csrf_token.get('value'):
                login_data[csrf_token['name']] = csrf_token['value']

            # Submit login
            response = self.session.post(
                self.LOGIN_URL,
                data=login_data,
                timeout=10,
                allow_redirects=True
            )

            # Check if login was successful
            # Common indicators: redirect to different page, presence of "logout" link
            if response.status_code == 200:
                # Check if we're still on login page (failed) or redirected (success)
                if 'login' not in response.url.lower() or 'logout' in response.text.lower():
                    logger.info("Login successful")
                    return True

            logger.error(f"Login may have failed (status: {response.status_code}, url: {response.url})")
            return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def _collect_blog_posts(self, max_posts: int = 10) -> List[Dict[str, Any]]:
        """
        Collect blog posts from blog feed.

        Args:
            max_posts: Maximum number of posts to collect

        Returns:
            List of blog post content items
        """
        posts = []

        try:
            # Get blog feed page
            response = self.session.get(self.BLOG_URL, timeout=10)

            if response.status_code != 200:
                logger.error(f"Failed to load blog feed: {response.status_code}")
                return posts

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find blog post elements
            # Common patterns: article tags, divs with class containing "post", "blog", "entry"
            post_elements = (
                soup.find_all('article') or
                soup.find_all('div', class_=re.compile(r'post|blog|entry', re.I)) or
                soup.find_all('div', class_=re.compile(r'content-item|feed-item', re.I))
            )

            logger.info(f"Found {len(post_elements)} potential blog posts")

            for i, post_elem in enumerate(post_elements[:max_posts]):
                try:
                    post_data = self._parse_blog_post(post_elem)
                    if post_data:
                        posts.append(post_data)
                except Exception as e:
                    logger.warning(f"Error parsing post {i+1}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error collecting blog posts: {e}")

        return posts

    def _parse_blog_post(self, post_elem) -> Optional[Dict[str, Any]]:
        """
        Parse a blog post element into standardized format.
        Visits individual post page to get full content and images.

        Args:
            post_elem: BeautifulSoup element containing post

        Returns:
            Standardized blog post content item
        """
        try:
            # Extract title
            title_elem = (
                post_elem.find('h1') or
                post_elem.find('h2') or
                post_elem.find('h3') or
                post_elem.find(class_=re.compile(r'title|heading', re.I))
            )
            title = title_elem.get_text(strip=True) if title_elem else "KT Technical Analysis Post"

            # Extract post URL
            link_elem = post_elem.find('a', href=True)
            post_url = link_elem['href'] if link_elem else self.BLOG_URL
            if post_url.startswith('/'):
                post_url = self.BASE_URL + post_url

            # Visit individual post page to get full content and images
            logger.info(f"Fetching full post: {title[:50]}...")
            full_content, images, date_text = self._fetch_full_post(post_url)

            # Download images (price charts)
            downloaded_images = []
            logger.info(f"Found {len(images)} images in post")
            for img_url in images[:10]:  # Limit to 10 images per post
                img_path = self._download_image(img_url, title)
                if img_path:
                    downloaded_images.append(str(img_path))

            # Build post data
            post_data = {
                "content_type": "blog_post",
                "url": post_url,
                "content_text": f"{title}\n\n{full_content}",
                "collected_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "title": title,
                    "published_date": date_text,
                    "num_images": len(downloaded_images),
                    "image_paths": downloaded_images,
                    "image_urls": images
                }
            }

            logger.info(f"Downloaded {len(downloaded_images)} chart images")
            return post_data

        except Exception as e:
            logger.error(f"Error parsing blog post: {e}")
            return None

    def _fetch_full_post(self, post_url: str) -> tuple:
        """
        Fetch full blog post content from individual post page.

        Args:
            post_url: URL of individual blog post

        Returns:
            Tuple of (content_text, image_urls, date_text)
        """
        try:
            response = self.session.get(post_url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch post page: {response.status_code}")
                return ("", [], None)

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract full content
            # Look for main content area (common WordPress patterns)
            content_elem = (
                soup.find('article') or
                soup.find(class_=re.compile(r'entry-content|post-content|content-area', re.I)) or
                soup.find('div', class_=re.compile(r'content', re.I))
            )

            content_text = ""
            if content_elem:
                # Get all text from paragraphs
                paragraphs = content_elem.find_all('p')
                content_text = '\n\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])

            # Extract date
            date_elem = soup.find(class_=re.compile(r'date|time|published', re.I))
            date_text = date_elem.get_text(strip=True) if date_elem else None

            # Extract all images from content area
            images = []
            if content_elem:
                img_elements = content_elem.find_all('img')
                for img in img_elements:
                    # Try multiple attributes where image URL might be
                    img_src = (
                        img.get('src') or
                        img.get('data-src') or
                        img.get('data-lazy-src') or
                        img.get('data-original')
                    )

                    if img_src:
                        # Make URL absolute
                        if img_src.startswith('/'):
                            img_src = self.BASE_URL + img_src
                        elif not img_src.startswith('http'):
                            img_src = self.BASE_URL + '/' + img_src

                        # Filter out small icons/logos (likely not price charts)
                        # Price charts are usually large images
                        if 'icon' not in img_src.lower() and 'logo' not in img_src.lower():
                            images.append(img_src)

            return (content_text, images, date_text)

        except Exception as e:
            logger.warning(f"Error fetching full post: {e}")
            return ("", [], None)

    def _download_image(self, url: str, post_title: str) -> Optional[Path]:
        """
        Download a chart image.

        Args:
            url: Image URL
            post_title: Blog post title (for filename)

        Returns:
            Path to downloaded image or None
        """
        try:
            # Download image
            response = self.session.get(url, timeout=30)

            if response.status_code != 200:
                logger.warning(f"Failed to download image: {response.status_code}")
                return None

            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'png' in content_type:
                ext = 'png'
            elif 'jpeg' in content_type or 'jpg' in content_type:
                ext = 'jpg'
            elif 'gif' in content_type:
                ext = 'gif'
            else:
                # Try to get from URL
                ext = url.split('.')[-1].lower()
                if ext not in ['png', 'jpg', 'jpeg', 'gif']:
                    ext = 'jpg'  # Default

            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', post_title)[:30]
            filename = f"{timestamp}_{safe_title}.{ext}"
            file_path = self.download_dir / filename

            # Save file
            with open(file_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"Downloaded image: {filename}")
            return file_path

        except Exception as e:
            logger.warning(f"Error downloading image: {e}")
            return None
