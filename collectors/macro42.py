"""
42 Macro Collector

Collects research reports and videos from app.42macro.com.
Requires email/password authentication.
"""

import requests
import logging
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class Macro42Collector(BaseCollector):
    """
    Collector for 42 Macro research content.

    Collects:
    - PDFs: Leadoff Morning Note, Around The Horn, Macro Scouting Report
    - Videos: Macro Minute daily videos
    - KISS Model: Portfolio signals and data
    """

    BASE_URL = "https://app.42macro.com"
    LOGIN_URL = f"{BASE_URL}/api/auth/login"

    def __init__(self, email: str, password: str):
        """
        Initialize 42 Macro collector.

        Args:
            email: 42macro account email
            password: 42macro account password
        """
        super().__init__(source_name="42macro")

        self.email = email
        self.password = password
        self.session = requests.Session()
        self.logged_in = False

        logger.info("Initialized Macro42Collector")

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect content from 42 Macro.

        Returns:
            List of collected content items
        """
        # Login first
        if not self.login():
            raise Exception("Failed to login to 42 Macro")

        collected_items = []

        # Collect PDFs
        logger.info("Collecting PDFs from 42 Macro...")
        pdfs = self._collect_pdfs()
        collected_items.extend(pdfs)

        # Collect videos
        logger.info("Collecting videos from 42 Macro...")
        videos = self._collect_videos()
        collected_items.extend(videos)

        logger.info(f"Collected {len(collected_items)} items from 42 Macro")
        return collected_items

    def login(self) -> bool:
        """
        Authenticate with 42 Macro.

        Returns:
            True if login successful
        """
        if self.logged_in:
            # Check if session is still valid
            if self._check_session():
                return True

        try:
            logger.info("Logging in to 42 Macro...")

            # Prepare login payload
            payload = {
                "email": self.email,
                "password": self.password
            }

            # Attempt login
            response = self.session.post(
                self.LOGIN_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )

            if response.status_code == 200:
                logger.info("Login successful")
                self.logged_in = True
                return True
            else:
                logger.error(f"Login failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def _check_session(self) -> bool:
        """
        Check if current session is still valid.

        Returns:
            True if session is valid
        """
        try:
            # Try to access a protected page
            response = self.session.get(f"{self.BASE_URL}/research")
            return response.status_code == 200
        except Exception:
            return False

    def _collect_pdfs(self) -> List[Dict[str, Any]]:
        """
        Collect PDF research reports.

        Returns:
            List of PDF content items
        """
        pdfs = []

        try:
            # Get research page
            response = self.session.get(f"{self.BASE_URL}/research")

            if response.status_code != 200:
                logger.error(f"Failed to fetch research page: {response.status_code}")
                return pdfs

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find PDF links (this is a placeholder - actual implementation
            # would need to be customized based on 42macro's actual HTML structure)
            # Common patterns:
            # - Links ending in .pdf
            # - S3 signed URLs
            # - Research report titles

            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf|s3\.amazonaws\.com'))

            for link in pdf_links:
                href = link.get('href')
                title = link.get_text(strip=True)

                # Download PDF
                pdf_path = self._download_pdf(href, title)

                if pdf_path:
                    pdfs.append({
                        "content_type": "pdf",
                        "file_path": str(pdf_path),
                        "url": href,
                        "content_text": title,
                        "collected_at": datetime.utcnow().isoformat(),
                        "metadata": {
                            "title": title,
                            "source_url": self.BASE_URL + "/research"
                        }
                    })

            logger.info(f"Collected {len(pdfs)} PDFs")

        except Exception as e:
            logger.error(f"Error collecting PDFs: {e}")

        return pdfs

    def _collect_videos(self) -> List[Dict[str, Any]]:
        """
        Collect video URLs and metadata.

        Returns:
            List of video content items
        """
        videos = []

        try:
            # Get videos page (placeholder - actual endpoint may differ)
            response = self.session.get(f"{self.BASE_URL}/videos")

            if response.status_code != 200:
                logger.warning(f"Videos page returned {response.status_code}")
                return videos

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find video elements (placeholder - customize based on actual HTML)
            # Look for:
            # - YouTube embeds
            # - Vimeo embeds
            # - Direct video URLs
            # - "Macro Minute" titles

            video_elements = soup.find_all(['iframe', 'video', 'a'],
                                          class_=re.compile(r'video|player|macro-minute', re.I))

            for element in video_elements:
                video_url = None
                title = ""

                # Extract URL based on element type
                if element.name == 'iframe':
                    video_url = element.get('src')
                elif element.name == 'a':
                    video_url = element.get('href')
                    title = element.get_text(strip=True)

                if video_url:
                    videos.append({
                        "content_type": "video",
                        "url": video_url,
                        "content_text": title or "42 Macro Video",
                        "collected_at": datetime.utcnow().isoformat(),
                        "metadata": {
                            "title": title,
                            "platform": self._detect_video_platform(video_url)
                        }
                    })

            logger.info(f"Collected {len(videos)} videos")

        except Exception as e:
            logger.error(f"Error collecting videos: {e}")

        return videos

    def _download_pdf(self, url: str, title: str) -> Optional[Path]:
        """
        Download a PDF file.

        Args:
            url: URL to download from
            title: Title for filename

        Returns:
            Path to downloaded file or None
        """
        try:
            # Make URL absolute if needed
            if not url.startswith('http'):
                url = self.BASE_URL + url

            # Download PDF
            response = self.session.get(url, stream=True)

            if response.status_code != 200:
                logger.error(f"Failed to download PDF: {response.status_code}")
                return None

            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', title)[:50]
            filename = f"{timestamp}_{safe_title}.pdf"
            file_path = self.download_dir / filename

            # Save file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded PDF: {filename}")
            return file_path

        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return None

    def _detect_video_platform(self, url: str) -> str:
        """
        Detect video platform from URL.

        Args:
            url: Video URL

        Returns:
            Platform name
        """
        url_lower = url.lower()

        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'vimeo.com' in url_lower:
            return 'vimeo'
        elif 'wistia.com' in url_lower:
            return 'wistia'
        else:
            return 'unknown'


# NOTE: The actual implementation would need to be customized based on
# 42macro's real HTML structure and API endpoints. This is a template
# that provides the framework. To complete it, you would need to:
#
# 1. Inspect the actual 42macro website HTML
# 2. Find the correct selectors for PDFs and videos
# 3. Identify if they use an API or just HTML scraping
# 4. Handle S3 signed URL expiration
# 5. Test with real credentials
