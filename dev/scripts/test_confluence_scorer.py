"""
Test script for Confluence Scorer Agent

Tests 7-pillar confluence scoring on sample analyzed content.
Uses mock data similar to what Phase 2 agents would produce.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.confluence_scorer import ConfluenceScorerAgent

# Load environment variables
load_dotenv()


# Sample analyzed content (simulating Phase 2 agent outputs)
SAMPLE_CONTENT_1 = {
    "source": "42macro",
    "content_type": "pdf",
    "key_themes": [
        "Disinflationary growth regime continuing",
        "Tech sector leadership intact",
        "Fed pause likely through Q1 2026",
        "Equity positioning light vs historical averages"
    ],
    "tickers_mentioned": ["SPY", "QQQ", "NVDA", "MSFT", "AAPL"],
    "sentiment": "bullish",
    "conviction": 8,
    "time_horizon": "3m",
    "market_regime": "disinflationary_growth",
    "positioning": {
        "equities": "underweight",
        "bonds": "neutral",
        "commodities": "underweight",
        "cash": "high"
    },
    "catalysts": [
        "CPI print Dec 12",
        "FOMC meeting Dec 18",
        "Tech earnings Q4"
    ],
    "falsification_criteria": [
        "If CPI >0.4% MoM for 2 consecutive months",
        "If SPY breaks 5600 on volume"
    ],
    "extracted_text": """
    We maintain our view that the US economy is in a disinflationary growth phase.
    PMIs across services and manufacturing continue to show expansion, while inflation
    metrics are moderating. The Fed is likely to pause rate adjustments through Q1 2026.

    Positioning data from CFTC shows equity futures positioning at 30th percentile vs
    5-year range, suggesting room for upside. Tech sector earnings growth is tracking
    15% YoY, with capex spend on AI infrastructure showing no signs of slowing.

    Valuation: SPX trading at 21x forward earnings, vs 10-year average of 18x, but
    justified by earnings growth trajectory. Implied earnings growth from current prices
    suggests market expects 12% for 2026.

    KISS Model positioning: 70% equities (tech overweight), 20% bonds, 10% cash.
    Tactically adding to tech LEAPs on pullbacks.
    """
}

SAMPLE_CONTENT_2 = {
    "source": "discord",
    "content_type": "image",
    "image_type": "volatility_surface",
    "tickers": ["SPX"],
    "sentiment": "neutral",
    "conviction": 5,
    "time_horizon": "1m",
    "interpretation": {
        "main_insight": "VIX term structure showing mild backwardation, suggesting near-term event risk",
        "key_levels": ["VIX 30d at 18%", "VIX 60d at 16.5%", "Put skew elevated at -2.5%"],
        "implied_volatility": {"30d": 0.18, "60d": 0.165, "90d": 0.155},
        "trend": "neutral",
        "positioning": "Heavy put buying at 5700 strike for Dec expiry, dealer short gamma"
    },
    "extracted_text": [
        "SPX Volatility Surface - Dec 2025",
        "30d IV: 18%",
        "60d IV: 16.5%",
        "90d IV: 15.5%",
        "Put/Call Skew: -2.5%"
    ],
    "actionable_levels": [
        "5700 put strike (high OI)",
        "5900 call strike (resistance)",
        "VIX 20 triggers protective put demand"
    ]
}

SAMPLE_CONTENT_3 = {
    "source": "kt_technical",
    "content_type": "image",
    "image_type": "technical_chart",
    "tickers": ["SPY"],
    "sentiment": "bullish",
    "conviction": 7,
    "time_horizon": "1m",
    "interpretation": {
        "main_insight": "SPY completing Elliott Wave 3, pullback to Wave 4 expected before final push",
        "key_levels": ["Support at 575", "Resistance at 595", "Target 610"],
        "support_resistance": {
            "support": ["575", "568", "560"],
            "resistance": ["595", "605", "610"]
        },
        "trend": "bullish",
        "technical_details": "Wave 3 extension complete, RSI overbought at 72, expecting healthy pullback to 575-580 for Wave 4 before final Wave 5 push to 610"
    },
    "actionable_levels": [
        "Buy zone: 575-580",
        "Stop loss: 568",
        "Target 1: 595",
        "Target 2: 610"
    ],
    "falsification_criteria": [
        "Break below 568 invalidates bullish count",
        "Failure to reclaim 575 after pullback"
    ]
}


def test_confluence_scorer():
    """Test confluence scorer with sample analyzed content."""

    print("=" * 80)
    print("CONFLUENCE SCORER AGENT TEST")
    print("=" * 80)

    # Initialize agent
    print("\n[1] Initializing Confluence Scorer Agent...")
    try:
        agent = ConfluenceScorerAgent()
        print("[OK] Agent initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize agent: {e}")
        return

    # Test samples
    samples = [
        ("42 Macro PDF Analysis", SAMPLE_CONTENT_1),
        ("Discord Volatility Chart", SAMPLE_CONTENT_2),
        ("KT Technical Chart", SAMPLE_CONTENT_3)
    ]

    print(f"\n[2] Testing {len(samples)} sample content pieces...")
    print("-" * 80)

    results = []

    for i, (name, content) in enumerate(samples, 1):
        print(f"\n[Test {i}/{len(samples)}] {name}")
        print(f"Source: {content.get('source', 'unknown')}")
        print(f"Type: {content.get('content_type', 'unknown')}")

        try:
            # Score content
            confluence_score = agent.analyze(
                analyzed_content=content,
                content_metadata={}
            )

            # Display results
            print(f"\n  === CONFLUENCE SCORE ===")
            print(f"  Core Total: {confluence_score['core_total']}/10")
            print(f"  Total Score: {confluence_score['total_score']}/14")
            print(f"  Confluence Level: {confluence_score['confluence_level'].upper()}")
            print(f"  Meets Threshold: {'YES' if confluence_score['meets_threshold'] else 'NO'}")

            print(f"\n  Pillar Scores:")
            for pillar in agent.ALL_PILLARS:
                score = confluence_score['pillar_scores'][pillar]
                pillar_display = pillar.replace("_", " ").title()
                print(f"    {pillar_display}: {score}/2")

            if confluence_score.get('primary_thesis'):
                print(f"\n  Primary Thesis:")
                print(f"    {confluence_score['primary_thesis']}")

            if confluence_score.get('variant_view'):
                print(f"\n  Variant View:")
                print(f"    {confluence_score['variant_view'][:150]}...")

            if confluence_score.get('p_and_l_mechanism'):
                print(f"\n  P&L Mechanism:")
                print(f"    {confluence_score['p_and_l_mechanism'][:150]}...")

            if confluence_score.get('falsification_criteria'):
                print(f"\n  Falsification Criteria:")
                for criterion in confluence_score['falsification_criteria'][:3]:
                    print(f"    - {criterion}")

            print(f"\n  [OK] Scoring successful")

            results.append({
                "name": name,
                "source": content.get('source'),
                "success": True,
                "core_total": confluence_score['core_total'],
                "total_score": confluence_score['total_score'],
                "confluence_level": confluence_score['confluence_level'],
                "meets_threshold": confluence_score['meets_threshold']
            })

        except Exception as e:
            print(f"\n  [ERROR] Scoring failed: {e}")
            results.append({
                "name": name,
                "source": content.get('source'),
                "success": False,
                "error": str(e)
            })

        print("-" * 80)

    # Summary
    print("\n[3] Test Summary")
    print("=" * 80)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\nTotal Tests: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print(f"\nSuccessful Scores:")
        for r in successful:
            print(f"  [OK] {r['name']} ({r['source']})")
            print(f"    - Core: {r['core_total']}/10, Total: {r['total_score']}/14")
            print(f"    - Level: {r['confluence_level'].upper()}, Threshold: {'YES' if r['meets_threshold'] else 'NO'}")

    if failed:
        print(f"\nFailed Scores:")
        for r in failed:
            print(f"  [ERROR] {r['name']} ({r['source']})")
            print(f"    Error: {r['error']}")

    # Save detailed results to JSON
    output_file = project_root / "test_output" / "confluence_scorer_test_results.json"
    output_file.parent.mkdir(exist_ok=True)

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
    test_confluence_scorer()
