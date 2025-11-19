"""
Debug script for KT Technical login flow.
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env')

BASE_URL = "https://kttechnicalanalysis.com"
LOGIN_URL = f"{BASE_URL}/login"
BLOG_URL = f"{BASE_URL}/blog-feed/"

def main():
    """Debug KT Technical login."""

    email = os.getenv('KT_EMAIL')
    password = os.getenv('KT_PASSWORD')

    print("="*60)
    print("DEBUGGING KT TECHNICAL LOGIN")
    print("="*60)
    print(f"Email: {email}")
    print(f"Password: {'*' * len(password)}")
    print()

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    # Step 1: Get login page
    print("Step 1: Fetching login page...")
    try:
        login_page = session.get(LOGIN_URL, timeout=10)
        print(f"  Status: {login_page.status_code}")
        print(f"  URL: {login_page.url}")
        print()

        # Parse login page
        soup = BeautifulSoup(login_page.content, 'html.parser')

        # Find all forms
        forms = soup.find_all('form')
        print(f"  Found {len(forms)} form(s)")

        for i, form in enumerate(forms):
            print(f"\n  Form {i+1}:")
            print(f"    Action: {form.get('action')}")
            print(f"    Method: {form.get('method')}")

            # Find all input fields
            inputs = form.find_all('input')
            print(f"    Input fields ({len(inputs)}):")
            for inp in inputs:
                print(f"      - name='{inp.get('name')}' type='{inp.get('type')}' value='{inp.get('value', '')[:20] if inp.get('value') else ''}'")

        # Save login page HTML for inspection
        debug_dir = project_root / 'debug'
        debug_dir.mkdir(exist_ok=True)

        with open(debug_dir / 'kt_login_page.html', 'w', encoding='utf-8') as f:
            f.write(login_page.text)
        print(f"\n  Saved login page HTML to: debug/kt_login_page.html")

    except Exception as e:
        print(f"  ERROR: {e}")
        return

    # Step 2: Try to login
    print("\n" + "-"*60)
    print("Step 2: Attempting login...")
    print("-"*60)

    try:
        # Build login payload
        login_data = {
            'email': email,
            'password': password
        }

        # Look for CSRF token or hidden fields
        hidden_fields = soup.find_all('input', {'type': 'hidden'})
        for field in hidden_fields:
            name = field.get('name')
            value = field.get('value')
            if name:
                login_data[name] = value
                print(f"  Added hidden field: {name}={value[:20] if value else ''}")

        print(f"\n  Submitting login to: {LOGIN_URL}")
        print(f"  Payload fields: {list(login_data.keys())}")

        # Submit login
        response = session.post(
            LOGIN_URL,
            data=login_data,
            timeout=10,
            allow_redirects=True
        )

        print(f"\n  Response status: {response.status_code}")
        print(f"  Final URL: {response.url}")
        print(f"  Content length: {len(response.content)} bytes")

        # Check for success indicators
        response_text = response.text.lower()

        if 'login' in response.url.lower():
            print("\n  ❌ Still on login page - login likely FAILED")
        elif 'logout' in response_text:
            print("\n  ✅ Found 'logout' in page - login likely SUCCESS")
        elif 'dashboard' in response.url.lower() or 'dashboard' in response_text:
            print("\n  ✅ Found 'dashboard' - login likely SUCCESS")
        else:
            print("\n  ⚠️ Unclear if login succeeded")

        # Save response for inspection
        with open(debug_dir / 'kt_login_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\n  Saved response HTML to: debug/kt_login_response.html")

    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Try to access blog feed
    print("\n" + "-"*60)
    print("Step 3: Accessing blog feed...")
    print("-"*60)

    try:
        blog_response = session.get(BLOG_URL, timeout=10)
        print(f"  Status: {blog_response.status_code}")
        print(f"  URL: {blog_response.url}")
        print(f"  Content length: {len(blog_response.content)} bytes")

        # Check if we're redirected back to login
        if 'login' in blog_response.url.lower():
            print("\n  ❌ Redirected to login - authentication FAILED")
        else:
            print("\n  ✅ Accessed blog feed - authentication SUCCESS")

            # Find blog posts
            soup = BeautifulSoup(blog_response.content, 'html.parser')
            articles = soup.find_all('article')
            posts = soup.find_all('div', class_=lambda x: x and ('post' in x.lower() or 'blog' in x.lower()))

            print(f"\n  Found {len(articles)} <article> tags")
            print(f"  Found {len(posts)} divs with 'post'/'blog' classes")

        # Save blog feed for inspection
        with open(debug_dir / 'kt_blog_feed.html', 'w', encoding='utf-8') as f:
            f.write(blog_response.text)
        print(f"\n  Saved blog feed HTML to: debug/kt_blog_feed.html")

    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*60)
    print("DEBUG COMPLETE")
    print("="*60)
    print("\nCheck the debug/ folder for saved HTML files to inspect.")


if __name__ == '__main__':
    main()
