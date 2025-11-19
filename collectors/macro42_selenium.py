"""
42 Macro Collector (Selenium Version)

Collects research reports and videos from app.42macro.com using Selenium.
Bypasses CloudFront WAF protection by using a real Chrome browser.
"""

import logging
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class Macro42Collector(BaseCollector):
    """
    Collector for 42 Macro research content using Selenium.

    Collects:
    - PDFs: Leadoff Morning Note, Around The Horn, Macro Scouting Report
    - Videos: Macro Minute daily videos
    - KISS Model: Portfolio signals (in weekly research PDFs)
    """

    BASE_URL = "https://app.42macro.com"
    LOGIN_URL = f"{BASE_URL}/login"

    def __init__(self, email: str, password: str, headless: bool = True):
        """
        Initialize 42 Macro collector.

        Args:
            email: 42macro account email
            password: 42macro account password
            headless: Run browser in headless mode (no visible window)
        """
        super().__init__(source_name="42macro")

        self.email = email
        self.password = password
        self.headless = headless
        self.driver = None

        logger.info("Initialized Macro42Collector (Selenium)")

    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect content from 42 Macro.

        Returns:
            List of collected content items
        """
        collected_items = []

        try:
            # Initialize browser
            self._init_driver()

            # Login
            if not self._login():
                raise Exception("Login failed")

            # Collect PDFs
            logger.info("Collecting PDFs from 42 Macro...")
            pdfs = self._collect_pdfs()
            collected_items.extend(pdfs)
            logger.info(f"Collected {len(pdfs)} PDFs")

            # Collect videos
            logger.info("Collecting videos from 42 Macro...")
            videos = self._collect_videos()
            collected_items.extend(videos)
            logger.info(f"Collected {len(videos)} videos")

        finally:
            # Always close browser
            if self.driver:
                self.driver.quit()

        logger.info(f"Total items collected from 42 Macro: {len(collected_items)}")
        return collected_items

    def _init_driver(self):
        """Initialize Chrome WebDriver with options."""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")

        # Additional options for better compatibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        # Initialize driver with webdriver-manager
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        logger.info("Chrome WebDriver initialized")

    def _login(self) -> bool:
        """
        Login to 42 Macro using Selenium.

        Returns:
            True if login successful
        """
        try:
            logger.info("Logging in to 42 Macro...")

            # Navigate to login page
            self.driver.get(self.LOGIN_URL)

            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)

            # Find and fill email field
            # Note: These selectors may need adjustment based on actual site
            try:
                email_field = wait.until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
            except:
                # Try alternative selectors
                email_field = wait.until(
                    EC.presence_of_element_located((By.NAME, "email"))
                )

            email_field.clear()
            email_field.send_keys(self.email)

            # Find and fill password field
            try:
                password_field = self.driver.find_element(By.ID, "password")
            except:
                password_field = self.driver.find_element(By.NAME, "password")

            password_field.clear()
            password_field.send_keys(self.password)

            # Find and click login button
            try:
                login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            except:
                login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log')]")

            login_button.click()

            # Wait for redirect (successful login usually redirects)
            wait.until(lambda driver: driver.current_url != self.LOGIN_URL)

            logger.info("Login successful")
            return True

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def _collect_pdfs(self) -> List[Dict[str, Any]]:
        """
        Collect PDF research reports.

        Returns:
            List of PDF content items
        """
        pdfs = []

        try:
            # Navigate to research page
            research_url = f"{self.BASE_URL}/research"
            self.driver.get(research_url)

            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Find PDF links
            # This is a generic approach - may need customization based on actual HTML
            pdf_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")

            # Also look for S3 signed URLs
            s3_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 's3.amazonaws.com')]")

            all_links = pdf_links + s3_links

            logger.info(f"Found {len(all_links)} PDF links")

            for link in all_links[:10]:  # Limit to most recent 10
                try:
                    href = link.get_attribute('href')
                    title = link.text or link.get_attribute('title') or "42 Macro Research"

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
                                "source_url": research_url
                            }
                        })

                except Exception as e:
                    logger.warning(f"Error processing PDF link: {e}")
                    continue

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
            # Navigate to videos page
            videos_url = f"{self.BASE_URL}/videos"
            self.driver.get(videos_url)

            # Wait for page to load
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Find video elements
            # Look for YouTube embeds
            youtube_iframes = self.driver.find_elements(By.XPATH, "//iframe[contains(@src, 'youtube.com')]")

            for iframe in youtube_iframes[:10]:  # Limit to most recent 10
                try:
                    src = iframe.get_attribute('src')

                    # Extract video ID from YouTube URL
                    video_id_match = re.search(r'youtube\.com/embed/([^?]+)', src)
                    if video_id_match:
                        video_id = video_id_match.group(1)
                        video_url = f"https://www.youtube.com/watch?v={video_id}"

                        videos.append({
                            "content_type": "video",
                            "url": video_url,
                            "content_text": "42 Macro Video",
                            "collected_at": datetime.utcnow().isoformat(),
                            "metadata": {
                                "title": "42 Macro Video",
                                "platform": "youtube",
                                "video_id": video_id
                            }
                        })

                except Exception as e:
                    logger.warning(f"Error processing video: {e}")
                    continue

        except Exception as e:
            logger.warning(f"Error collecting videos: {e}")

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
            import requests

            # Download PDF
            response = requests.get(url, timeout=30)

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
                f.write(response.content)

            logger.info(f"Downloaded PDF: {filename}")
            return file_path

        except Exception as e:
            logger.error(f"Error downloading PDF: {e}")
            return None
