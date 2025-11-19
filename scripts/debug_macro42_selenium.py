"""
Debug script for 42 Macro Selenium collector.
Runs browser in non-headless mode so we can see what's happening.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env')

BASE_URL = "https://app.42macro.com"
LOGIN_URL = f"{BASE_URL}/login"

def main():
    """Debug 42 Macro Selenium collector."""

    email = os.getenv('MACRO42_EMAIL')
    password = os.getenv('MACRO42_PASSWORD')

    print("="*60)
    print("DEBUGGING 42 MACRO SELENIUM COLLECTOR")
    print("="*60)
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print("\nNote: Browser will be visible (not headless)")
    print("This helps us see what's happening")
    print()

    # Initialize Chrome with visible browser
    chrome_options = Options()
    # NO headless mode - we want to see the browser
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Step 1: Navigate to login page
        print("Step 1: Navigating to login page...")
        driver.get(LOGIN_URL)
        time.sleep(3)  # Wait for page to load

        print(f"  Current URL: {driver.current_url}")
        print(f"  Page title: {driver.title}")

        # Save page source
        debug_dir = project_root / 'debug'
        debug_dir.mkdir(exist_ok=True)

        with open(debug_dir / 'macro42_login_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"  Saved login page HTML to: debug/macro42_login_page.html")

        # Find form elements
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        forms = soup.find_all('form')
        print(f"\n  Found {len(forms)} form(s)")

        for i, form in enumerate(forms):
            print(f"\n  Form {i+1}:")
            print(f"    Action: {form.get('action')}")
            print(f"    Method: {form.get('method')}")

            inputs = form.find_all('input')
            print(f"    Input fields ({len(inputs)}):")
            for inp in inputs:
                print(f"      - name='{inp.get('name')}' id='{inp.get('id')}' type='{inp.get('type')}'")

        # Step 2: Try to login
        print("\n" + "-"*60)
        print("Step 2: Attempting login...")
        print("-"*60)

        wait = WebDriverWait(driver, 10)

        # Try to find email field
        try:
            print("\n  Looking for email field...")
            email_field = wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            print("    Found by ID 'email'")
        except:
            try:
                email_field = driver.find_element(By.NAME, "email")
                print("    Found by NAME 'email'")
            except:
                try:
                    email_field = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
                    print("    Found by CSS selector input[type='email']")
                except Exception as e:
                    print(f"    ERROR: Could not find email field: {e}")
                    return

        # Try to find password field
        try:
            print("\n  Looking for password field...")
            password_field = driver.find_element(By.ID, "password")
            print("    Found by ID 'password'")
        except:
            try:
                password_field = driver.find_element(By.NAME, "password")
                print("    Found by NAME 'password'")
            except:
                try:
                    password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                    print("    Found by CSS selector input[type='password']")
                except Exception as e:
                    print(f"    ERROR: Could not find password field: {e}")
                    return

        # Fill in credentials
        print("\n  Filling in credentials...")
        email_field.clear()
        email_field.send_keys(email)
        password_field.clear()
        password_field.send_keys(password)
        print("    Credentials entered")

        # Find and click login button
        try:
            print("\n  Looking for login button...")
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            print("    Found submit button")
        except:
            try:
                login_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Log')]")
                print("    Found button with 'Log' text")
            except Exception as e:
                print(f"    ERROR: Could not find login button: {e}")
                return

        print("  Clicking login button...")
        login_button.click()

        # Wait for redirect
        print("  Waiting for page to load...")
        time.sleep(5)  # Give it time to log in

        print(f"\n  Current URL: {driver.current_url}")
        print(f"  Page title: {driver.title}")

        # Check if login was successful
        if 'login' in driver.current_url.lower():
            print("\n  WARNING: Still on login page - login may have FAILED")
        else:
            print("\n  SUCCESS: Redirected away from login page")

        # Save post-login page
        with open(debug_dir / 'macro42_after_login.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"  Saved post-login HTML to: debug/macro42_after_login.html")

        # Step 3: Try to access research page
        print("\n" + "-"*60)
        print("Step 3: Navigating to research page...")
        print("-"*60)

        research_url = f"{BASE_URL}/research"
        driver.get(research_url)
        time.sleep(3)

        print(f"  Current URL: {driver.current_url}")
        print(f"  Page title: {driver.title}")

        # Look for PDF links
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
        print(f"\n  Found {len(pdf_links)} links with '.pdf' in href")

        s3_links = soup.find_all('a', href=lambda x: x and 's3.amazonaws.com' in x.lower())
        print(f"  Found {len(s3_links)} links with 's3.amazonaws.com' in href")

        # Look for any links
        all_links = soup.find_all('a', href=True)
        print(f"  Total <a> tags with href: {len(all_links)}")

        # Show first 10 links
        print("\n  First 10 links:")
        for i, link in enumerate(all_links[:10]):
            href = link.get('href', '')
            text = link.get_text(strip=True)[:50]
            print(f"    {i+1}. {text} -> {href[:80]}")

        # Save research page
        with open(debug_dir / 'macro42_research_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"\n  Saved research page HTML to: debug/macro42_research_page.html")

        # Step 4: Try to access videos page
        print("\n" + "-"*60)
        print("Step 4: Navigating to videos page...")
        print("-"*60)

        videos_url = f"{BASE_URL}/videos"
        driver.get(videos_url)
        time.sleep(3)

        print(f"  Current URL: {driver.current_url}")
        print(f"  Page title: {driver.title}")

        # Look for YouTube iframes
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        youtube_iframes = soup.find_all('iframe', src=lambda x: x and 'youtube.com' in x.lower())
        print(f"\n  Found {len(youtube_iframes)} YouTube iframes")

        # Look for video elements
        video_tags = soup.find_all('video')
        print(f"  Found {len(video_tags)} <video> tags")

        # Save videos page
        with open(debug_dir / 'macro42_videos_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"\n  Saved videos page HTML to: debug/macro42_videos_page.html")

        print("\n" + "="*60)
        print("DEBUG COMPLETE")
        print("="*60)
        print("\nKeeping browser open for 10 seconds so you can inspect...")
        print("Check the debug/ folder for saved HTML files.")
        time.sleep(10)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nClosing browser...")
        driver.quit()


if __name__ == '__main__':
    main()
