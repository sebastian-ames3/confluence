"""
Test script for Image Intelligence Agent

Tests image analysis on real sample charts from:
- Discord (Options Insight volatility charts)
- KT Technical (price charts with Elliott Wave analysis)
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.image_intelligence import ImageIntelligenceAgent

# Load environment variables
load_dotenv()


def test_image_intelligence():
    """Test image intelligence agent with sample charts."""

    print("=" * 80)
    print("IMAGE INTELLIGENCE AGENT TEST")
    print("=" * 80)

    # Initialize agent
    print("\n[1] Initializing Image Intelligence Agent...")
    try:
        agent = ImageIntelligenceAgent()
        print("[OK] Agent initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
        return

    # Find sample images
    downloads_dir = project_root / "downloads"
    discord_images = list((downloads_dir / "discord").glob("*.png"))[:5]  # First 5
    kt_images = list((downloads_dir / "kt_technical").glob("*.png"))[:5]  # First 5

    all_images = discord_images + kt_images

    print(f"\n[2] Found sample images:")
    print(f"    - Discord: {len(discord_images)} images (testing first 5)")
    print(f"    - KT Technical: {len(kt_images)} images (testing first 5)")
    print(f"    - Total to test: {len(all_images)} images")

    if not all_images:
        print("\n[ERROR] No images found for testing")
        print(f"Expected images in: {downloads_dir}")
        return

    # Test each image
    print("\n[3] Testing Image Analysis...")
    print("-" * 80)

    results = []

    for i, image_path in enumerate(all_images[:3], 1):  # Test first 3 images
        print(f"\n[Test {i}/{min(3, len(all_images))}] {image_path.name}")
        print(f"Source: {image_path.parent.name}")

        # Determine source
        if "discord" in str(image_path):
            source = "discord"
            context = "Options Insight volatility analysis"
        elif "kt_technical" in str(image_path):
            source = "kt_technical"
            context = "Technical price chart analysis"
        else:
            source = "unknown"
            context = None

        try:
            # Analyze image
            analysis = agent.analyze(
                image_path=str(image_path),
                source=source,
                context=context,
                metadata={}
            )

            # Display results
            print(f"\n  Image Type: {analysis.get('image_type', 'unknown')}")
            print(f"  Tickers: {', '.join(analysis.get('tickers', []))}")
            print(f"  Sentiment: {analysis.get('sentiment', 'unknown')}")
            print(f"  Conviction: {analysis.get('conviction', 0)}/10")
            print(f"  Time Horizon: {analysis.get('time_horizon', 'unknown')}")

            interpretation = analysis.get('interpretation', {})
            if interpretation.get('main_insight'):
                print(f"\n  Main Insight:")
                print(f"    {interpretation['main_insight']}")

            if interpretation.get('key_levels'):
                print(f"\n  Key Levels ({len(interpretation['key_levels'])}):")
                for level in interpretation['key_levels'][:5]:
                    print(f"    - {level}")

            if interpretation.get('support_resistance'):
                sr = interpretation['support_resistance']
                if sr.get('support'):
                    print(f"\n  Support: {', '.join(map(str, sr['support'][:3]))}")
                if sr.get('resistance'):
                    print(f"  Resistance: {', '.join(map(str, sr['resistance'][:3]))}")

            if interpretation.get('implied_volatility'):
                iv = interpretation['implied_volatility']
                print(f"\n  Implied Volatility:")
                for period, value in iv.items():
                    if value is not None:
                        print(f"    {period}: {value}")

            if analysis.get('actionable_levels'):
                print(f"\n  Actionable Levels:")
                for level in analysis['actionable_levels'][:3]:
                    print(f"    - {level}")

            if analysis.get('extracted_text'):
                print(f"\n  Extracted Text: {len(analysis['extracted_text'])} items")

            print(f"\n  [OK] Analysis successful")

            results.append({
                "image": image_path.name,
                "source": source,
                "success": True,
                "image_type": analysis.get('image_type', 'unknown'),
                "tickers": analysis.get('tickers', []),
                "conviction": analysis.get('conviction', 0),
                "sentiment": analysis.get('sentiment', 'unknown')
            })

        except Exception as e:
            print(f"\n  [ERROR] Analysis failed: {e}")
            results.append({
                "image": image_path.name,
                "source": source,
                "success": False,
                "error": str(e)
            })

        print("-" * 80)

    # Summary
    print("\n[4] Test Summary")
    print("=" * 80)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\nTotal Images Tested: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print(f"\nSuccessful Analyses:")
        for r in successful:
            print(f"  [OK] {r['image']} ({r['source']})")
            print(f"    - Type: {r['image_type']}, Tickers: {', '.join(r['tickers'][:3])}, "
                  f"Conviction: {r['conviction']}/10, Sentiment: {r['sentiment']}")

    if failed:
        print(f"\nFailed Analyses:")
        for r in failed:
            print(f"  [ERROR] {r['image']} ({r['source']})")
            print(f"    Error: {r['error']}")

    # Save detailed results to JSON
    output_file = project_root / "test_output" / "image_intelligence_test_results.json"
    output_file.parent.mkdir(exist_ok=True)

    # Save full results (excluding binary data)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")
    print("\n" + "=" * 80)

    if len(successful) == len(results):
        print("[OK] ALL TESTS PASSED")
    elif len(successful) > 0:
        print(f"[WARN] PARTIAL SUCCESS ({len(successful)}/{len(results)} passed)")
    else:
        print("[ERROR] ALL TESTS FAILED")

    print("=" * 80)


if __name__ == "__main__":
    test_image_intelligence()
