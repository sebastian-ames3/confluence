"""
42 Macro Collector (Selenium Version)

Collects research reports and videos from app.42macro.com using Selenium.
Bypasses CloudFront WAF protection by using a real Chrome browser.

Cookie Persistence: Saves cookies after successful login to avoid WAF red flags
from repeated logins. Only re-authenticates when cookies expire.
"""

import logging
import re
import pickle
import random
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

# Pool of real browser User-Agents for rotation (reduces fingerprinting)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


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
    COOKIES_FILE = "temp/42macro_cookies.pkl"  # Cookie persistence file

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

        # Ensure temp directory exists for cookies
        Path("temp").mkdir(exist_ok=True)

        logger.info("Initialized Macro42Collector (Selenium) with cookie persistence")

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

            # Try to load cookies first, only login if cookies don't work
            if not self._try_load_session():
                # Fresh login required
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
        """Initialize Chrome WebDriver with options and random User-Agent."""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")

        # Configure download directory
        prefs = {
            "download.default_directory": str(self.download_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True  # Don't open PDFs in browser
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Rotate User-Agent to reduce fingerprinting (WAF evasion)
        user_agent = random.choice(USER_AGENTS)
        chrome_options.add_argument(f"--user-agent={user_agent}")
        logger.info(f"Using User-Agent: {user_agent[:50]}...")

        # Additional options for better compatibility
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        # Initialize driver with webdriver-manager
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        logger.info(f"Chrome WebDriver initialized, downloads to: {self.download_dir}")

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

            # Save cookies for next time to avoid repeated logins (WAF red flag)
            self._save_cookies()

            return True

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def _try_load_session(self) -> bool:
        """
        Try to load saved cookies and verify session is still valid.

        Returns:
            True if session restored successfully
        """
        try:
            cookies_path = Path(self.COOKIES_FILE)

            if not cookies_path.exists():
                logger.info("No saved cookies found - fresh login required")
                return False

            logger.info("Found saved cookies - attempting to restore session")

            # Load cookies
            self._load_cookies()

            # Navigate to a protected page to test if session is valid
            self.driver.get(f"{self.BASE_URL}/research")

            # Check if we got redirected to login (session expired)
            if "login" in self.driver.current_url.lower():
                logger.info("Session expired - fresh login required")
                return False

            logger.info("✓ Session restored from cookies - skipping login")
            return True

        except Exception as e:
            logger.warning(f"Failed to restore session from cookies: {e}")
            return False

    def _save_cookies(self):
        """Save current browser cookies to file."""
        try:
            cookies = self.driver.get_cookies()
            with open(self.COOKIES_FILE, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info(f"Saved {len(cookies)} cookies to {self.COOKIES_FILE}")
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    def _load_cookies(self):
        """Load cookies from file into browser."""
        try:
            # Must navigate to domain first before adding cookies
            self.driver.get(self.BASE_URL)

            with open(self.COOKIES_FILE, 'rb') as f:
                cookies = pickle.load(f)

            for cookie in cookies:
                # Remove 'expiry' if it's in the past to avoid errors
                if 'expiry' in cookie:
                    del cookie['expiry']
                self.driver.add_cookie(cookie)

            logger.info(f"Loaded {len(cookies)} cookies from {self.COOKIES_FILE}")
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")

    def _collect_pdfs(self) -> List[Dict[str, Any]]:
        """
        Collect PDF research reports from React SPA.

        42 Macro uses a React app that renders content dynamically.
        PDFs are presented as cards, not direct links.

        Returns:
            List of PDF content items
        """
        import time
        import os
        from glob import glob

        pdfs = []

        try:
            # Navigate to research page
            research_url = f"{self.BASE_URL}/research"
            self.driver.get(research_url)

            # Wait for React app to render content
            wait = WebDriverWait(self.driver, 15)

            # Wait for research cards to appear
            try:
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".cursor-pointer.bg-card")
                ))
            except:
                logger.warning("Research cards not found - page may not have loaded")
                return pdfs

            # Give extra time for all cards to render
            time.sleep(2)

            # Find all research card elements
            cards = self.driver.find_elements(By.CSS_SELECTOR, ".cursor-pointer.bg-card.p-2.rounded-xl")

            logger.info(f"Found {len(cards)} research cards")

            for idx, card in enumerate(cards[:10]):  # Limit to most recent 10
                try:
                    # Extract report type (e.g., "Leadoff Morning Note", "Around the Horn")
                    type_elem = card.find_element(By.CSS_SELECTOR, ".capitalize")
                    report_type = type_elem.text.strip()

                    # Extract date (e.g., "Tuesday, November 18, 2025")
                    date_elem = card.find_element(By.CSS_SELECTOR, ".text-select.font-bold")
                    date_text = date_elem.text.strip()

                    # Check if locked (has lock icon)
                    is_locked = False
                    try:
                        card.find_element(By.CSS_SELECTOR, "svg.text-white.absolute")
                        is_locked = True
                    except:
                        pass

                    # Skip locked content
                    if is_locked:
                        logger.info(f"Skipping locked content: {report_type} - {date_text}")
                        continue

                    title = f"{report_type} - {date_text}"
                    logger.info(f"Downloading: {title}")

                    # Get list of files before download
                    before_files = set(glob(str(self.download_dir / "*.pdf")))

                    # Try to find and click download button
                    try:
                        # Look for download button (has download icon)
                        download_btn = card.find_element(By.CSS_SELECTOR, ".ml-auto.mr-6")

                        # Scroll to element to ensure it's clickable
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", download_btn)
                        time.sleep(0.5)

                        # Click the download button
                        download_btn.click()

                        # Wait for download to start and complete (max 15 seconds)
                        download_complete = False
                        for _ in range(30):  # Check every 0.5 seconds for 15 seconds
                            time.sleep(0.5)
                            after_files = set(glob(str(self.download_dir / "*.pdf")))
                            new_files = after_files - before_files

                            # Check if we have a new file that's not a .crdownload
                            for new_file in new_files:
                                if not new_file.endswith('.crdownload'):
                                    pdf_path = Path(new_file)
                                    download_complete = True
                                    break

                            if download_complete:
                                break

                        if not download_complete:
                            logger.warning(f"Download timeout for: {title}")
                            continue

                        # Rename file to something more descriptive
                        safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', title)[:80]
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_filename = f"{timestamp}_{safe_title}.pdf"
                        new_path = self.download_dir / new_filename

                        pdf_path.rename(new_path)
                        logger.info(f"Downloaded and renamed: {new_filename}")

                        # Create content item with downloaded file
                        pdfs.append({
                            "content_type": "pdf",
                            "file_path": str(new_path),
                            "url": research_url,
                            "content_text": title,
                            "collected_at": datetime.utcnow().isoformat(),
                            "metadata": {
                                "title": title,
                                "report_type": report_type,
                                "date": date_text,
                                "is_locked": is_locked,
                                "source_url": research_url,
                                "file_size_mb": round(new_path.stat().st_size / (1024 * 1024), 2)
                            }
                        })

                    except Exception as e:
                        logger.warning(f"Error downloading PDF for '{title}': {e}")
                        continue

                except Exception as e:
                    logger.warning(f"Error processing research card {idx}: {e}")
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
