"""
Test Analysis Pipeline - Sample Run

Analyzes a small sample of collected content to test the full pipeline.
Uses the API endpoints to trigger classification and analysis.
"""

import requests
import time
import json

API_BASE = "http://localhost:8000/api"

def test_analysis_pipeline():
    """Test the analysis pipeline on a few items."""

    print("=" * 80)
    print("TESTING ANALYSIS PIPELINE - 3 VIDEO SAMPLE")
    print("=" * 80)

    # Step 1: Check what's pending
    print("\n[1] Checking pending analysis...")
    response = requests.get(f"{API_BASE}/analyze/pending")
    pending_data = response.json()

    print(f"Total pending: {pending_data['total_pending']}")
    print(f"By source: {pending_data['by_source']}")

    # Step 2: Run batch classification on 3 items
    print("\n[2] Running classification on 3 videos...")
    response = requests.post(
        f"{API_BASE}/analyze/classify-batch",
        params={"limit": 3, "only_unprocessed": True}
    )

    if response.status_code == 200:
        batch_result = response.json()
        print(f"✅ Classified {batch_result['count']} items")

        for item in batch_result['results']:
            if 'error' in item:
                print(f"  ❌ ID {item['raw_content_id']}: {item['error']}")
            else:
                print(f"  ✅ ID {item['raw_content_id']}: {item['classification']} (priority: {item['priority']})")
                print(f"     Route to: {', '.join(item['route_to'])}")
    else:
        print(f"❌ Classification failed: {response.status_code}")
        print(response.text)
        return

    # Step 3: Check analysis stats
    print("\n[3] Checking analysis statistics...")
    response = requests.get(f"{API_BASE}/analyze/stats")
    stats = response.json()

    print(f"Total raw content: {stats['total_raw_content']}")
    print(f"Total processed: {stats['total_processed']}")
    print(f"Processing rate: {stats['processing_rate']}%")
    print(f"By agent type: {stats['by_agent_type']}")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Check your dashboard at http://localhost:8000")
    print("2. Go to 'Source Browser' to see analyzed content")
    print("3. Check 'Themes' page for extracted themes")
    print("\nNote: This only ran classification. Full analysis (transcript")
    print("extraction, confluence scoring) requires additional API integration.")

if __name__ == "__main__":
    try:
        test_analysis_pipeline()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API at http://localhost:8000")
        print("Make sure the FastAPI server is running:")
        print("  python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ Error: {e}")
